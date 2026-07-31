from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import require_consent, get_db
from app.models.user import User
from app.models.snippets import Snippet
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

router = APIRouter(prefix="/snippets", tags=["Snippets"])

class SnippetCreate(BaseModel):
    title: str
    content: str
    language: str = "text"
    tags: List[str] = []

class SnippetResponse(BaseModel):
    id: UUID
    title: str
    content: str
    language: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[SnippetResponse])
def list_snippets(
    db: Session = Depends(get_db),
    user: User = Depends(require_consent)
):
    return db.query(Snippet).filter(Snippet.user_id == user.id).order_by(Snippet.created_at.desc()).all()

@router.post("/", response_model=SnippetResponse)
def create_snippet(
    payload: SnippetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_consent)
):
    snippet = Snippet(
        user_id=user.id,
        title=payload.title,
        content=payload.content,
        language=payload.language,
        tags=payload.tags
    )
    db.add(snippet)
    db.commit()
    db.refresh(snippet)
    return snippet

@router.delete("/{snippet_id}")
def delete_snippet(
    snippet_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_consent)
):
    snippet = db.query(Snippet).filter(Snippet.id == snippet_id, Snippet.user_id == user.id).first()
    if not snippet:
        raise HTTPException(status_code=404, detail="Snippet not found")
    
    db.delete(snippet)
    db.commit()
    return {"status": "deleted"}
