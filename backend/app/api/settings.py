from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.user import User
from app.core.deps import get_current_user
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["Settings"])

# ─── Default settings ────────────────────────────────────────────────────────
DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "system",
    "accentColor": "default",
    "language": "auto",
    "spokenLanguage": "auto",
    "selectedVoice": "af_sky",
    "separateVoice": True,
    "fontSize": "medium",
    "showAvatars": True,
    "sendOnEnter": True,
    "model": "llama-3.1-8b-instant",
    "temperature": 0.7,
    "maxTokens": 2048,
    "topP": 1.0,
    "frequencyPenalty": 0.0,
    "presencePenalty": 0.0,
    "historyLimit": 0,
    "activeModel": "llama-3.1-8b-instant",
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
    logger.info(f"Retrieved settings for user {current_user.email}: {saved}")
    # Merge: defaults first, then saved values override
    merged = {**DEFAULT_SETTINGS, **saved}
    return merged


@router.post("/settings")
def save_settings(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Persist the user's settings to the database."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Only persist keys that exist in DEFAULT_SETTINGS to keep DB clean
    filtered = {k: v for k, v in payload.items() if k in DEFAULT_SETTINGS}
    logger.info(f"Saving settings for user {current_user.email}: {filtered}")
    
    # Update the user settings field
    user.settings = filtered
    db.add(user)
    db.commit()
    return {"status": "saved"}
