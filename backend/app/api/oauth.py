from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import settings
from app.core.auth import create_access_token
from app.database.db import SessionLocal
from app.models.user import User
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["OAuth"])

class GoogleLoginRequest(BaseModel):
    credential: str

@router.post("/google")
async def google_login(payload: GoogleLoginRequest):
    """Verify Google OAuth token and return JWT"""
    try:
        # Verify the Google token
        idinfo = id_token.verify_oauth2_token(
            payload.credential,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=60
        )
        
        # Extract user info
        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")
        google_id = idinfo.get("sub")
        
        if not email:
            raise HTTPException(400, "Email not provided by Google")
        
        # Check if user exists, create if not
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Create new user
                user = User(
                    username=email.split("@")[0],
                    email=email,
                    avatar_url=picture,
                    hashed_password="",  # No password for OAuth users
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"Created new user via Google OAuth: {email}")
            elif picture and user.avatar_url != picture:
                # Always sync photo for existing user if it changed
                user.avatar_url = picture
                db.commit()
                db.refresh(user)
                logger.info(f"Synced profile photo for user: {email}")
            
            # Generate JWT token
            token = create_access_token(
                data={"sub": str(user.id)},
                expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "avatar_url": user.avatar_url, # Top level for consistency
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "picture": user.avatar_url,
                    "id": str(user.id)
                }
            }
        finally:
            db.close()
            
    except ValueError as e:
        print(f"DEBUG: Google token verification failed: {e}")
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(401, f"Invalid Google token: {str(e)}")
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        raise HTTPException(500, f"OAuth error: {str(e)}")
