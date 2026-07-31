"""Legal / consent endpoints.

``GET  /legal/consent``  — current consent status for the caller.
``POST /legal/consent``  — accept (or re-accept) the current policy versions.
``POST /legal/consent/withdraw`` — withdraw consent (GDPR Art. 7(3)).
``GET  /legal/versions`` — public: which policy versions are current.

These endpoints intentionally depend on ``get_current_user`` rather than
``require_consent``. Gating them behind the consent check would deadlock a
stale user: they could not consent because they had not consented.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import limiter
from app.models.user import User
from app.services import consent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/legal", tags=["Legal"])


class ConsentRequest(BaseModel):
    """Explicit, affirmative consent. Both flags must be true.

    Versions are echoed back by the client so a user cannot accidentally
    accept a policy version different from the one they were shown — if the
    policy changed while the modal was open, the request is rejected and the
    client re-fetches.
    """
    accept_terms: bool = False
    accept_privacy: bool = False
    terms_version: str | None = None
    privacy_version: str | None = None


class ConsentStatusResponse(BaseModel):
    consent_current: bool
    accepted_terms_version: str | None
    accepted_privacy_version: str | None
    required_terms_version: str
    required_privacy_version: str
    consent_accepted_at: str | None


class VersionsResponse(BaseModel):
    terms_version: str
    privacy_version: str


@router.get("/versions", response_model=VersionsResponse)
def get_versions():
    """Public: the policy versions currently in force.

    Unauthenticated so the login and registration screens can render the
    correct version alongside the checkboxes.
    """
    return VersionsResponse(
        terms_version=settings.CURRENT_TERMS_VERSION,
        privacy_version=settings.CURRENT_PRIVACY_VERSION,
    )


@router.get("/consent", response_model=ConsentStatusResponse)
def get_consent(current_user: User = Depends(get_current_user)):
    """Consent status for the authenticated caller."""
    return ConsentStatusResponse(**consent_service.consent_status(current_user))


@router.post("/consent", response_model=ConsentStatusResponse)
@limiter.limit("10/minute")
def post_consent(
    request: Request,
    payload: ConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept the current Terms and Privacy Policy.

    Requires both flags explicitly true. Records version, timestamp, IP, and
    user agent, and appends an append-only audit row.
    """
    if not payload.accept_terms or not payload.accept_privacy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONSENT_INCOMPLETE",
                "message": (
                    "Both the Terms of Service and the Privacy Policy must be "
                    "accepted."
                ),
                "accept_terms": payload.accept_terms,
                "accept_privacy": payload.accept_privacy,
            },
        )

    # Reject a stale client: the user must have been shown the version they
    # are accepting. Omitted versions are allowed for older clients.
    if payload.terms_version is not None and payload.terms_version != settings.CURRENT_TERMS_VERSION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "VERSION_MISMATCH",
                "message": "The Terms of Service have changed. Please review the current version.",
                "required_terms_version": settings.CURRENT_TERMS_VERSION,
            },
        )
    if payload.privacy_version is not None and payload.privacy_version != settings.CURRENT_PRIVACY_VERSION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "VERSION_MISMATCH",
                "message": "The Privacy Policy has changed. Please review the current version.",
                "required_privacy_version": settings.CURRENT_PRIVACY_VERSION,
            },
        )

    had_consented_before = current_user.consent_accepted_at is not None
    event_type = (
        consent_service.EVENT_RECONSENT if had_consented_before else consent_service.EVENT_ACCEPT
    )

    consent_service.record_consent(db, current_user, request=request, event_type=event_type)
    db.commit()
    db.refresh(current_user)

    logger.info("Consent recorded (%s) for user %s", event_type, current_user.id)
    return ConsentStatusResponse(**consent_service.consent_status(current_user))


@router.post("/consent/withdraw", response_model=ConsentStatusResponse)
@limiter.limit("5/minute")
def withdraw_consent(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Withdraw consent (GDPR Art. 7(3)).

    Clears current consent so the gate blocks protected endpoints, and appends
    a ``withdraw`` audit row. The account is **not** deleted — withdrawal and
    erasure are separate rights. Auth, consent, and account-deletion endpoints
    stay reachable afterwards so the user can still act on their data.
    """
    consent_service.record_withdrawal(db, current_user, request=request)
    db.commit()
    db.refresh(current_user)

    logger.info("Consent withdrawn for user %s", current_user.id)
    return ConsentStatusResponse(**consent_service.consent_status(current_user))
