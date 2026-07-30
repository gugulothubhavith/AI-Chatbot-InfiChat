from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.auth import decode_token
from app.database.db import get_db
from sqlalchemy.orm import Session
from app.models.user import User
import logging
import uuid

logger = logging.getLogger(__name__)

security = HTTPBearer()

from fastapi.security import SecurityScopes
from app.models.api_keys import PersonalAccessToken
import hashlib
from datetime import datetime, timezone

async def get_current_user(
    security_scopes: SecurityScopes,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    token = credentials.credentials
    user = None
    token_scopes = []
    
    if token.startswith("sk_infi_"):
        # API Key auth
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        pat = db.query(PersonalAccessToken).filter(
            PersonalAccessToken.token_hash == token_hash,
            PersonalAccessToken.is_active == True
        ).first()
        if not pat:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
                headers={"WWW-Authenticate": authenticate_value},
            )

        # Expired tokens must stop working. expires_at is stored naive on
        # SQLite and aware on Postgres, so normalise before comparing —
        # a TypeError here would otherwise 500 instead of rejecting.
        if pat.expires_at is not None:
            expires_at = pat.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired",
                    headers={"WWW-Authenticate": authenticate_value},
                )

        # Update last used
        pat.last_used_at = datetime.now(timezone.utc)
        db.commit()

        user = db.query(User).filter(User.id == pat.user_id).first()
        token_scopes = pat.scopes
    else:
        # JWT Auth (assumes full access for now)
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": authenticate_value},
            )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        try:
            uuid_obj = uuid.UUID(user_id)
        except ValueError:
            logger.error("Malformed token subject received")
            raise HTTPException(status_code=401, detail="Invalid token")
            
        user = db.query(User).filter(User.id == uuid_obj).first()
        token_scopes = ["full_access"]

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": authenticate_value},
        )

    # Deactivated accounts must lose access immediately. Without this check a
    # banned user keeps full access until their JWT expires (up to an hour),
    # and their API keys keep working indefinitely.
    # NULL is treated as active so pre-existing rows are never locked out.
    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    # Check scopes
    if security_scopes.scopes and "full_access" not in token_scopes:
        for scope in security_scopes.scopes:
            if scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required scope: {scope}",
                    headers={"WWW-Authenticate": authenticate_value},
                )
                
    return user

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> User | None:
    if not credentials:
        return None
        
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        return None
        
    user_id: str = payload.get("sub")
    if not user_id:
        return None

    try:
        uuid_obj = uuid.UUID(user_id)
    except ValueError:
        return None

    user = db.query(User).filter(User.id == uuid_obj).first()

    # Mirror get_current_user: a deactivated account is treated as anonymous
    # rather than returned to callers as a valid identity.
    if user is not None and user.is_active is False:
        return None

    return user