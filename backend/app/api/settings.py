from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.user import User
from app.core.deps import get_current_user
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List, Literal
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["Settings"])

# ─── Pydantic validation schema ──────────────────────────────────────────────
class SettingsUpdate(BaseModel):
    """Partial update schema — all fields optional, with validation."""
    theme: Optional[Literal["light", "dark", "system"]] = None
    accentColor: Optional[str] = None
    language: Optional[str] = None
    spokenLanguage: Optional[str] = None
    selectedVoice: Optional[str] = None
    separateVoice: Optional[bool] = None
    fontSize: Optional[Literal["small", "medium", "large"]] = None
    showAvatars: Optional[bool] = None
    sendOnEnter: Optional[bool] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    maxTokens: Optional[int] = Field(None, ge=1, le=128000)
    topP: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequencyPenalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presencePenalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    historyLimit: Optional[int] = Field(None, ge=0)
    activeModel: Optional[str] = None
    autoSendVoice: Optional[bool] = None
    textToSpeech: Optional[bool] = None
    notifResponses: Optional[List[str]] = None
    notifRecommendations: Optional[List[str]] = None
    notifUsage: Optional[List[str]] = None
    customInstructions: Optional[str] = None
    nickname: Optional[str] = None
    occupation: Optional[str] = None
    moreAboutYou: Optional[str] = None
    enableMemory: Optional[bool] = None
    enableChatHistory: Optional[bool] = None
    enableCodeInterpreter: Optional[bool] = None
    enableVoice: Optional[bool] = None

# ─── Default settings ────────────────────────────────────────────────────────
DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "dark",
    "accentColor": "default",
    "language": "auto",
    "spokenLanguage": "auto",
    "selectedVoice": "af_sky",
    "separateVoice": True,
    "fontSize": "medium",
    "showAvatars": True,
    "sendOnEnter": True,
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "temperature": 0.7,
    "maxTokens": 2048,
    "topP": 1.0,
    "frequencyPenalty": 0.0,
    "presencePenalty": 0.0,
    "historyLimit": 0,
    "activeModel": "nvidia/nemotron-3-ultra-550b-a55b",
    "autoSendVoice": True,
    "textToSpeech": False,
    "notifResponses": ["push"],
    "notifRecommendations": ["push"],
    "notifUsage": ["push"],
    "customInstructions": "",
    "nickname": "",
    "occupation": "",
    "moreAboutYou": "",
    "enableMemory": True,
    "enableChatHistory": True,
    "enableCodeInterpreter": True,
    "enableVoice": True,
}

@router.get("/settings")
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the user's saved settings merged with defaults."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    saved = user.settings or {}
    logger.info(f"Retrieved settings for user_id={current_user.id}")
    # Merge: defaults first, then saved values override
    merged = {**DEFAULT_SETTINGS, **saved}
    return merged


@router.post("/settings")
def save_settings(
    payload: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Persist the user's settings to the database with validation."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only persist non-None fields (partial update support)
    update_data = payload.model_dump(exclude_none=True)
    
    # Only persist keys that exist in DEFAULT_SETTINGS to keep DB clean
    filtered = {k: v for k, v in update_data.items() if k in DEFAULT_SETTINGS}
    logger.info(f"Saving {len(filtered)} settings for user_id={current_user.id}")
    
    # Merge with existing settings (partial update)
    existing = user.settings or {}
    existing.update(filtered)
    user.settings = existing
    db.add(user)
    db.commit()
    return {"status": "saved"}
