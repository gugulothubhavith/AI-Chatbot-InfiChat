from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import settings
from app.core.auth import create_access_token
from app.database.db import SessionLocal
from app.models.user import User
from datetime import timedelta
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["OAuth"])

class GoogleLoginRequest(BaseModel):
    credential: str


def _upsert_google_user(email: str, name: str, picture: str | None) -> dict:
    """Find-or-create the user for a verified Google profile, then mint a JWT.

    Synchronous by design: the caller runs this in a worker thread via
    ``asyncio.to_thread`` so the DB round-trips stay off the event loop. Opens
    and closes its own Session because a Session must not cross threads.

    Returns plain values only — never the ORM instance, which would be detached
    the moment this function's Session closes.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        is_new_user = user is None
        if is_new_user:
            user = User(
                username=name or email.split("@")[0],
                email=email,
                avatar_url=picture,
                hashed_password="",  # No password for OAuth users
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user via Google OAuth: {email}")
        else:
            # Always sync photo and name for existing user if it changed or was missing
            changed = False
            if picture and (not user.avatar_url or user.avatar_url != picture):
                user.avatar_url = picture
                changed = True
                logger.info(f"Synced profile photo for user: {email}")
            if name and user.username != name:
                user.username = name
                changed = True
                logger.info(f"Synced name for user: {email}")

            if changed:
                db.commit()
                db.refresh(user)
            elif not picture:
                logger.warning(f"No picture URL received from Google info for {email}")

        # Read every attribute into a local before the Session closes.
        user_id = str(user.id)
        username = user.username
        user_email = user.email
        avatar_url = user.avatar_url
        role = user.role.value if getattr(user, "role", None) else "user"

        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "name": username,
            "email": user_email,
            "avatar_url": avatar_url,
            "is_new_user": is_new_user,
            "role": role,
        }
    finally:
        db.close()


@router.post("/google")
async def google_login(payload: GoogleLoginRequest):
    """Verify Google OAuth token and return JWT"""
    try:
        # Determine if it's an access token (ya29.) or an id_token (eyJ...)
        if payload.credential.startswith("ya29."):
            async with httpx.AsyncClient() as client:
                # 1. Verify token audience
                token_info_resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?access_token={payload.credential}")
                if token_info_resp.status_code != 200:
                    raise ValueError("Invalid Google access token")
                token_info = token_info_resp.json()
                
                # The audience check must fail closed. A token that names a
                # different client — or one whose aud/azp tokeninfo omits — is
                # not ours, and accepting it would let any Google app's token
                # log a user in here.
                if not settings.GOOGLE_CLIENT_ID:
                    raise ValueError("GOOGLE_CLIENT_ID is not configured")

                azp = token_info.get("azp")
                aud = token_info.get("aud")
                if settings.GOOGLE_CLIENT_ID not in (azp, aud):
                    logger.warning(
                        "Google token aud/azp mismatch: got aud=%r azp=%r", aud, azp
                    )
                    raise ValueError("Token was not issued to this client")
                
                # 2. Get user info
                user_info_resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo", 
                    headers={"Authorization": f"Bearer {payload.credential}"}
                )
                if user_info_resp.status_code != 200:
                    raise ValueError("Failed to fetch Google user info")
                idinfo = user_info_resp.json()
        else:
            # Verify the Google ID token
            idinfo = id_token.verify_oauth2_token(
                payload.credential,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=60
            )
        
        # Extract user info
        # Don't log the whole profile — it carries email, name and photo URL
        # into the log file on every single sign-in.
        logger.debug("Google profile verified (sub=%s)", idinfo.get("sub"))
        email = idinfo.get("email")
        
        # Robustly extract the user's first and last name from Google profile
        given_name = idinfo.get("given_name", "").strip()
        family_name = idinfo.get("family_name", "").strip()
        name = idinfo.get("name", "").strip()
        
        if not name:
            if given_name or family_name:
                name = f"{given_name} {family_name}".strip()
            else:
                name = email.split("@")[0]
        
        picture = idinfo.get("picture")
        google_id = idinfo.get("sub")
        
        if not email:
            raise HTTPException(400, "Email not provided by Google")
        
        # Upsert the user and mint the token in a worker thread. Everything
        # below is synchronous SQLAlchemy, and this is an ``async def``, so
        # inline it would run on the event loop and stall every concurrent
        # request — including in-flight SSE streams — for the round-trip.
        #
        # Returns a plain dict: the ORM instance is bound to the Session this
        # thread closes, so handing it back would risk DetachedInstanceError.
        # Signing the JWT is local CPU work, safe to do here.
        return await asyncio.to_thread(
            _upsert_google_user, email, name, picture
        )

    except ValueError as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(401, f"Invalid Google token: {str(e)}")
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(500, f"OAuth error: {str(e)}")
