from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.user import User
from app.models.api_keys import PersonalAccessToken
from app.core.deps import get_current_user
from pydantic import BaseModel
from typing import List, Optional
import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_keys", tags=["API Keys"])

class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = ["full_access"]

class APIKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: List[str]
    created_at: str
    last_used_at: Optional[str]

@router.get("/", response_model=List[APIKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tokens = db.query(PersonalAccessToken).filter(
        PersonalAccessToken.user_id == current_user.id,
        PersonalAccessToken.is_active == True
    ).all()
    
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "prefix": t.prefix,
            "scopes": t.scopes,
            "created_at": t.created_at.isoformat() if t.created_at else "",
            "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None
        } for t in tokens
    ]

@router.post("/")
def create_api_key(
    req: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Generate a secure token
    raw_token = f"sk_infi_{secrets.token_hex(16)}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    prefix = raw_token[:12] + "..."
    
    new_token = PersonalAccessToken(
        user_id=current_user.id,
        name=req.name,
        token_hash=token_hash,
        prefix=prefix,
        scopes=req.scopes
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    
    return {
        "id": str(new_token.id),
        "name": new_token.name,
        "token": raw_token, # ONLY time it is returned
        "prefix": new_token.prefix,
        "scopes": new_token.scopes,
        "created_at": new_token.created_at.isoformat()
    }

@router.delete("/{token_id}")
def delete_api_key(
    token_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = db.query(PersonalAccessToken).filter(
        PersonalAccessToken.id == token_id,
        PersonalAccessToken.user_id == current_user.id
    ).first()
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
        
    db.delete(token)
    db.commit()
    return {"status": "success"}
