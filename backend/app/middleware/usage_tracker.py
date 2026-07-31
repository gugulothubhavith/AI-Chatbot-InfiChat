"""Usage tracking middleware — enforces subscription limits on API requests.

Intercepts API calls to:
1. Validate user's feature access based on subscription plan
2. Check usage limits before processing requests
3. Return 402/429 with upgrade info if limits exceeded
4. Record usage after successful responses

NOTE: This middleware resolves the caller independently since middleware runs
before route-level Depends() resolvers. It understands both JWT bearer tokens
and personal access tokens (``sk_infi_`` prefix) so API-key traffic is metered
the same as browser traffic.

Fail-closed policy: metering is a paid-plan control. If we cannot determine a
caller's entitlements because the database or a limit check errors out, we
return 503 rather than silently granting free, unmetered access. The one
deliberate "allow" path is a fresh install with no plans seeded yet, which the
subscription service signals explicitly (not via an exception).
"""

import hashlib
import json
import logging
import time
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.auth import decode_token
from app.services.subscription_service import (
    get_feature_from_path,
    check_feature_access,
    check_usage_limit,
    record_usage,
)

logger = logging.getLogger(__name__)

# Paths to skip for usage tracking (including /api/v1/ variants)
SKIP_PATHS = {
    "/auth/", "/docs", "/openapi", "/health", "/static",
    "/subscription/", "/api/v1/subscription/",
    "/admin/", "/api/v1/admin/",
    "/metrics", "/login", "/register",
}

# Path prefixes to track
TRACK_PREFIXES = ("/api/v1/", "/chat/", "/research/", "/thinking/", "/code/", "/image/", "/rag/", "/voice/", "/web_search/")

_SERVICE_UNAVAILABLE = Response(
    content=json.dumps({
        "detail": "Usage metering is temporarily unavailable. Please retry shortly.",
        "code": "METERING_UNAVAILABLE",
    }),
    status_code=503,
    media_type="application/json",
)


def _service_unavailable() -> Response:
    # Return a fresh Response each time — Starlette Responses are single-use.
    return Response(
        content=_SERVICE_UNAVAILABLE.body,
        status_code=503,
        media_type="application/json",
    )


def _resolve_user_id(request: Request, db) -> Optional[str]:
    """Resolve the caller's user id from a JWT or personal access token.

    Returns None only when there is no usable credential. Raises on database
    errors so the caller can fail closed rather than mistaking an outage for an
    anonymous request.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    if not token:
        return None

    if token.startswith("sk_infi_"):
        # Personal access token — hash and look up the owner. A DB error here
        # propagates so dispatch() fails closed.
        from app.models.api_keys import PersonalAccessToken

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        pat = db.query(PersonalAccessToken).filter(
            PersonalAccessToken.token_hash == token_hash,
            PersonalAccessToken.is_active == True,  # noqa: E712
        ).first()
        if not pat:
            return None
        return str(pat.user_id)

    # JWT — decode is local and needs no database.
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("sub")


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware that tracks API usage and enforces subscription limits."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Skip non-tracked paths
        path = request.url.path
        if not any(path.startswith(prefix) for prefix in TRACK_PREFIXES):
            return await call_next(request)

        if any(path.startswith(skip) for skip in SKIP_PATHS):
            return await call_next(request)

        # Skip WebSocket
        if path.startswith("/ws"):
            return await call_next(request)

        # Determine feature from path before touching the DB.
        feature = get_feature_from_path(path)
        if not feature:
            return await call_next(request)

        # Open a session. If the primary DB is unavailable we cannot know the
        # caller's entitlements, so we refuse the request (fail closed) instead
        # of handing out free access.
        try:
            from app.database.db import SessionLocal
            db = SessionLocal()
        except Exception as e:
            logger.error(f"UsageTracking: DB unavailable, refusing request: {e}")
            return _service_unavailable()

        try:
            # Resolve the caller. Unauthenticated requests are passed through so
            # the route's own auth dependency can issue the correct 401 — the
            # firewall/auth layer owns that decision, not metering.
            try:
                user_id = _resolve_user_id(request, db)
            except Exception as e:
                logger.error(f"UsageTracking: credential lookup failed, refusing request: {e}")
                return _service_unavailable()

            if not user_id:
                return await call_next(request)

            # Entitlement + limit checks. A raised exception here means we
            # genuinely don't know the caller's limits — fail closed.
            try:
                has_access = check_feature_access(user_id, feature, db)
            except Exception as e:
                logger.error(f"UsageTracking: feature-access check failed, refusing request: {e}")
                return _service_unavailable()

            if not has_access:
                return Response(
                    content=json.dumps({
                        "detail": (
                            f"The '{feature}' feature is not available on your current plan. "
                            f"Upgrade to access this feature."
                        ),
                        "code": "FEATURE_NOT_AVAILABLE",
                        "feature": feature,
                    }),
                    status_code=402,
                    media_type="application/json",
                    headers={"X-Upgrade-Required": "true"},
                )

            try:
                allowed, remaining, limit = check_usage_limit(user_id, feature, db)
            except Exception as e:
                logger.error(f"UsageTracking: usage-limit check failed, refusing request: {e}")
                return _service_unavailable()

            if not allowed:
                return Response(
                    content=json.dumps({
                        "detail": (
                            f"You've reached your daily/monthly limit for '{feature}' "
                            f"({limit} uses). Please upgrade your plan or wait for the reset."
                        ),
                        "code": "LIMIT_EXCEEDED",
                        "feature": feature,
                        "limit": limit,
                        "remaining": 0,
                    }),
                    status_code=429,
                    media_type="application/json",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-Upgrade-Required": "true",
                    },
                )

            # Process the request exactly once. Metering has already been checked
            # and the entitlement decision made — the DB session must be returned
            # to the pool NOW (not after call_next) so that an SSE stream or any
            # long-running request doesn't pin a connection for the whole stream
            # and starve parallel users.
            db.close()
            db = None  # prevent the outer finally from double-closing

            start_time = time.time()
            response = await call_next(request)
            elapsed = time.time() - start_time

            # Add usage headers
            response.headers["X-Usage-Feature"] = feature
            response.headers["X-Usage-Remaining"] = str(max(0, remaining - 1))
            response.headers["X-Usage-Limit"] = str(limit)

            # Record usage for successful responses on a brand-new session so
            # the pool connection budget is returned to the rest of the app the
            # moment the response starts streaming. A recording failure must
            # not fail the already-served request, so it is logged and
            # swallowed here (and only here).
            if 200 <= response.status_code < 400:
                try:
                    from app.database.db import SessionLocal
                    rec_db = SessionLocal()
                    try:
                        record_usage(user_id, feature, db=rec_db)
                    finally:
                        rec_db.close()
                except Exception as e:
                    logger.error(f"Usage recording failed: {e}")

            return response
        finally:
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass
