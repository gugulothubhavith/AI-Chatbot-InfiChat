from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from app.services.indic_voice_service import indic_voice_service
from app.schemas.voice import TTSRequest
from app.core.deps import get_current_user
from app.models.user import User
import shutil
import os
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])

UPLOAD_DIR = "/tmp/uploads/voice"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    try:
        # Save temp file
        ext = file.filename.split('.')[-1] if '.' in file.filename else "wav"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Transcribe (fallback to legacy for now or update later)
        from app.services import voice_service as legacy_service
        text = await legacy_service.transcribe_audio(filepath)
        
        # Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if not text:
             raise HTTPException(status_code=500, detail="Transcription failed or empty")
             
        return {"text": text}
        
    except Exception as e:
        logger.error(f"Transcription API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Highly advanced professional Indic TTS streaming."""
    try:
        if not request.text:
             raise HTTPException(status_code=400, detail="Text is required")
             
        return StreamingResponse(
            indic_voice_service.synthesize_professional_stream(
                request.text, 
                voice_id=request.voice_id or "hi_female"
            ),
            media_type="audio/mpeg"
        )
    except Exception as e:
        logger.error(f"[API ERROR] TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
