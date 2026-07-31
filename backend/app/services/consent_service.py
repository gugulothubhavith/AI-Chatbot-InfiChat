"""Consent recording and staleness checks.

Single source of truth for "has this user accepted the current policies?".
Both the auth endpoints (registration, OAuth) and the request-time gate in
``app/core/deps.py`` route through here so the rule cannot drift between them.

Design notes
------------
* ``consent_events`` is append-only. A withdrawal is a new row with
  ``event_type='withdraw'``, never an update or delete of an earlier row —
  GDPR Art. 7(1) requires being able to *demonstrate* consent was obtained,
  which an overwritten row cannot do.
* The denormalised columns on ``users`` are the fast path. The gate runs on
  every authenticated request, so it must not need a second query.
* ``None`` means "never consented" and is stale. Existing users are all NULL
  after the migration, so they are prompted to consent on their next request
  rather than silently grandfathered — a user who never saw the policy has
  not agreed to it.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.consent import ConsentEvent
from app.models.user import User

logger = logging.getLogger(__name__)

# Event type values written to ConsentEvent.event_type
EVENT_ACCEPT = "accept"
EVENT_RECONSENT = "re-consent"
EVENT_WITHDRAW = "withdraw"

# Cap stored audit metadata. A hostile client can send a multi-kilobyte
# User-Agent, and these columns are unbounded VARCHAR.
_MAX_UA_LENGTH = 512
_MAX_IP_LENGTH = 64


def client_ip(request: Optional[Request]) -> Optional[str]:
    """Best-effort client IP for the consent audit record.

    Only trusts ``X-Forwarded-For`` when the immediate peer is a configured
    trusted proxy — otherwise any client could forge the IP recorded against
    their own consent, which would undermine the audit trail's evidential
    value.
    """
    if request is None:
        return None

    peer = request.client.host if request.client else None

    trusted = settings.trusted_proxy_ips
    if peer and trusted and peer in trusted:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            # Left-most entry is the original client.
            candidate = forwarded.split(",")[0].strip()
            if candidate:
                return candidate[:_MAX_IP_LENGTH]

    return peer[:_MAX_IP_LENGTH] if peer else None


def client_user_agent(request: Optional[Request]) -> Optional[str]:
    """Truncated User-Agent for the consent audit record."""
    if request is None:
        return None
    ua = request.headers.get("user-agent")
    return ua[:_MAX_UA_LENGTH] if ua else None


def is_consent_current(user: User) -> bool:
    """True when the user has accepted both current policy versions.

    NULL (never consented) is stale by design — see the module docstring.
    """
    return (
        user.terms_accepted_version == settings.CURRENT_TERMS_VERSION
        and user.privacy_accepted_version == settings.CURRENT_PRIVACY_VERSION
    )


def consent_status(user: User) -> dict:
    """Serialisable consent state for ``GET /legal/consent``."""
    accepted_at = user.consent_accepted_at
    return {
        "consent_current": is_consent_current(user),
        "accepted_terms_version": user.terms_accepted_version,
        "accepted_privacy_version": user.privacy_accepted_version,
        "required_terms_version": settings.CURRENT_TERMS_VERSION,
        "required_privacy_version": settings.CURRENT_PRIVACY_VERSION,
        "consent_accepted_at": accepted_at.isoformat() if accepted_at else None,
    }


def record_consent(
    db: Session,
    user: User,
    request: Optional[Request] = None,
    event_type: str = EVENT_ACCEPT,
) -> ConsentEvent:
    """Record acceptance of the current policy versions.

    Updates the denormalised columns on ``users`` and appends an audit row.
    Does **not** commit — the caller owns the transaction so consent and the
    surrounding work (user creation, for instance) land atomically.
    """
    now = datetime.now(timezone.utc)
    ip = client_ip(request)
    user_agent = client_user_agent(request)

    user.terms_accepted_version = settings.CURRENT_TERMS_VERSION
    user.privacy_accepted_version = settings.CURRENT_PRIVACY_VERSION
    user.consent_accepted_at = now
    user.consent_ip = ip
    user.consent_user_agent = user_agent

    event = ConsentEvent(
        user_id=user.id,
        event_type=event_type,
        terms_version=settings.CURRENT_TERMS_VERSION,
        privacy_version=settings.CURRENT_PRIVACY_VERSION,
        ip_address=ip,
        user_agent=user_agent,
        timestamp=now,
    )
    db.add(event)
    return event


def record_withdrawal(
    db: Session,
    user: User,
    request: Optional[Request] = None,
) -> ConsentEvent:
    """Record withdrawal of consent (GDPR Art. 7(3)).

    Clears the current-state columns so the gate blocks the user until they
    consent again, and appends a ``withdraw`` audit row. Earlier acceptance
    rows are left untouched — the history is the evidence that consent was
    once validly given.

    Does not commit; the caller owns the transaction.
    """
    now = datetime.now(timezone.utc)

    user.terms_accepted_version = None
    user.privacy_accepted_version = None
    user.consent_accepted_at = None

    event = ConsentEvent(
        user_id=user.id,
        event_type=EVENT_WITHDRAW,
        terms_version=None,
        privacy_version=None,
        ip_address=client_ip(request),
        user_agent=client_user_agent(request),
        timestamp=now,
    )
    db.add(event)
    return event
