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

import asyncio
import hashlib
import json
import logging
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

# Methods that never consume quota. Feature resolution is a substring match on
# the path, so ``GET /chat/sessions`` and ``GET /chat/{id}/messages`` resolve to
# the ``chat_messages`` feature just like ``POST /chat/stream`` does. Metering
# them meant simply opening the app burned generation quota, and a user who hit
# their limit was locked out of reading their own history.
#
# Safe to skip because every metered generator is a POST — /chat/message,
# /chat/stream, /research/stream, /thinking/stream, /web_search/stream,
# /image/generate, /code/*, /rag/upload, /rag/query, /voice/*. No GET route
# invokes a model, so this cannot be used to bypass billing. Keep it that way:
# a new generating endpoint must be POST.
UNMETERED_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

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


def _resolve_user_id(auth_header: str, db) -> Optional[str]:
    """Resolve the caller's user id from a JWT or personal access token.

    Takes the raw ``Authorization`` header rather than the ``Request`` so this
    stays a pure synchronous function that is safe to run in a worker thread.

    Returns None only when there is no usable credential. Raises on database
    errors so the caller can fail closed rather than mistaking an outage for an
    anonymous request.
    """
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


def _check_entitlements(auth_header: str, feature: str) -> dict:
    """Run the whole metering gate synchronously and return a verdict.

    Every database call for one request is grouped here so the caller can hand
    the lot to a single worker thread. Previously each of these ran directly on
    the event loop; because the loop is single-threaded, a sync round-trip here
    froze *every* concurrent request — measurably stalling in-flight SSE streams
    by the duration of the query. Returning a plain dict (rather than a
    ``Response``) keeps this function free of any loop-bound object.

    Opens and closes its own session so no connection is pinned for the life of
    the downstream request, which for a stream can be minutes.
    """
    try:
        from app.database.db import SessionLocal
        db = SessionLocal()
    except Exception as e:
        logger.error(f"UsageTracking: DB unavailable, refusing request: {e}")
        return {"verdict": "unavailable"}

    try:
        # Unauthenticated requests pass through so the route's own auth
        # dependency can issue the correct 401 — the auth layer owns that
        # decision, not metering.
        try:
            user_id = _resolve_user_id(auth_header, db)
        except Exception as e:
            logger.error(f"UsageTracking: credential lookup failed, refusing request: {e}")
            return {"verdict": "unavailable"}

        if not user_id:
            return {"verdict": "anonymous"}

        try:
            if not check_feature_access(user_id, feature, db):
                return {"verdict": "no_access", "user_id": user_id}
        except Exception as e:
            logger.error(f"UsageTracking: feature-access check failed, refusing request: {e}")
            return {"verdict": "unavailable"}

        try:
            allowed, remaining, limit = check_usage_limit(user_id, feature, db)
        except Exception as e:
            logger.error(f"UsageTracking: usage-limit check failed, refusing request: {e}")
            return {"verdict": "unavailable"}

        if not allowed:
            return {"verdict": "over_limit", "user_id": user_id, "limit": limit}

        return {
            "verdict": "allowed",
            "user_id": user_id,
            "remaining": remaining,
            "limit": limit,
        }
    finally:
        try:
            db.close()
        except Exception:
            pass


def _record_usage_sync(user_id: str, feature: str) -> None:
    """Record one usage event on its own short-lived session."""
    from app.database.db import SessionLocal

    rec_db = SessionLocal()
    try:
        record_usage(user_id, feature, db=rec_db)
    finally:
        rec_db.close()


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

        # Reads neither consume quota nor require the feature flag. See
        # UNMETERED_METHODS: this is what stops "open the app" from spending
        # generation credits.
        if request.method.upper() in UNMETERED_METHODS:
            return await call_next(request)

        # Determine feature from path before touching the DB.
        feature = get_feature_from_path(path)
        if not feature:
            return await call_next(request)

        # Run the entire metering gate in a worker thread. The checks are
        # synchronous SQLAlchemy, and the event loop is shared by every live
        # request — running them inline froze all concurrent traffic for the
        # duration of the queries, including SSE streams already mid-flight.
        # The session is opened and closed inside the thread, so no connection
        # is pinned across the downstream request.
        auth_header = request.headers.get("Authorization", "")
        gate = await asyncio.to_thread(_check_entitlements, auth_header, feature)
        verdict = gate["verdict"]

        if verdict == "unavailable":
            return _service_unavailable()

        if verdict == "anonymous":
            return await call_next(request)

        if verdict == "no_access":
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

        if verdict == "over_limit":
            limit = gate["limit"]
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

        user_id = gate["user_id"]
        remaining = gate["remaining"]
        limit = gate["limit"]

        response = await call_next(request)

        response.headers["X-Usage-Feature"] = feature
        response.headers["X-Usage-Remaining"] = str(max(0, remaining - 1))
        response.headers["X-Usage-Limit"] = str(limit)

        # Record usage for successful responses, also off-loop. A recording
        # failure must not fail an already-served request, so it is logged and
        # swallowed here (and only here).
        if 200 <= response.status_code < 400:
            try:
                await asyncio.to_thread(_record_usage_sync, user_id, feature)
            except Exception as e:
                logger.error(f"Usage recording failed: {e}")

        return response
