"""Admin audit trail — records every request to the admin API.

The write is synchronous SQLAlchemy, so it runs in a worker thread. Doing it
inline on the event loop blocked every other in-flight request (including live
SSE streams) for the duration of two queries, and the audit record is never
worth stalling unrelated traffic for.
"""

import asyncio
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.auth import decode_token
from app.database.db import SessionLocal
from app.models.admin import AdminAuditLog, AdminProfile

logger = logging.getLogger(__name__)


def _write_audit_log(
    user_id: str | None,
    action: str,
    path: str,
    ip_address: str,
    user_agent: str | None,
    status_code: int,
    query_params: dict,
) -> None:
    """Resolve the acting admin and persist one audit row.

    Takes only plain values so it is safe to run off the event loop — nothing
    here touches the Request or Response objects. Both queries share one
    session; the previous version opened two.
    """
    db = SessionLocal()
    try:
        admin_id = None
        if user_id:
            admin = (
                db.query(AdminProfile)
                .filter(AdminProfile.user_id == user_id)
                .first()
            )
            if admin:
                admin_id = admin.id

        db.add(
            AdminAuditLog(
                admin_id=admin_id,
                action=action,
                resource_type="API_ENDPOINT",
                resource_id=path,
                ip_address=ip_address,
                user_agent=user_agent,
                new_state={"status_code": status_code, "query_params": query_params},
            )
        )
        db.commit()
    finally:
        db.close()


class AdminAuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/api/admin"):
            return await call_next(request)

        response = await call_next(request)

        # Decoding the token is local and cheap; only the DB write is offloaded.
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header[7:])
            if payload:
                user_id = payload.get("sub")

        try:
            await asyncio.to_thread(
                _write_audit_log,
                user_id,
                f"{request.method} {request.url.path}",
                request.url.path,
                request.client.host if request.client else "unknown",
                request.headers.get("user-agent"),
                response.status_code,
                dict(request.query_params),
            )
        except Exception as e:
            # An audit write must never fail a request that already succeeded,
            # but it must be visible in the logs rather than printed to stdout.
            logger.error("Failed to record admin audit log: %s", e, exc_info=True)

        return response
