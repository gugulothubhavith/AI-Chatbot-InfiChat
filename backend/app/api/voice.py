from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from app.services.indic_voice_service import indic_voice_service
from app.services import voice_service
from app.schemas.voice import TTSRequest
from app.core.deps import get_current_user
from app.models.user import User
import tempfile
import os
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])

# Use platform-safe temp directory
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "uploads", "voice")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Audio uploads are streamed to disk, so cap them to stop a single request
# filling the volume. ~25 MB comfortably fits several minutes of speech.
MAX_AUDIO_BYTES = 25 * 1024 * 1024
_CHUNK = 1024 * 1024

# Only accept containers the transcriber can actually decode.
ALLOWED_AUDIO_EXTENSIONS = {"wav", "webm", "mp3", "m4a", "ogg", "flac", "mp4"}


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    filepath = None
    try:
        # Derive the extension from the client filename but never trust it as a
        # path component — os.path.basename + allowlist prevents traversal.
        raw_ext = ""
        if file.filename and "." in file.filename:
            raw_ext = os.path.basename(file.filename).rsplit(".", 1)[-1].lower()
        ext = raw_ext if raw_ext in ALLOWED_AUDIO_EXTENSIONS else "wav"

        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Stream to disk with a hard ceiling instead of copyfileobj, which
        # would happily write an unbounded upload.
        written = 0
        with open(filepath, "wb") as buffer:
            while chunk := await file.read(_CHUNK):
                written += len(chunk)
                if written > MAX_AUDIO_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Audio exceeds {MAX_AUDIO_BYTES // (1024 * 1024)} MB limit",
                    )
                buffer.write(chunk)

        if written == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio is empty")

        text = await voice_service.transcribe_audio(filepath)

        if not text or text.startswith("[Error"):
             raise HTTPException(status_code=500, detail="Transcription failed or empty")

        return {"text": text}

    except HTTPException:
        raise
    except Exception as e:
        # Log the detail, return a generic message — exception text can carry
        # filesystem paths and internal state.
        logger.error(f"Transcription API error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")
    finally:
        # Always cleanup temp file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    user: User = Depends(get_current_user),
):
    """Professional Indic TTS streaming via Edge-TTS.

    Requires authentication: synthesis is unbounded compute, and an open
    endpoint lets anyone burn CPU on arbitrary text. Length is capped in
    TTSRequest.
    """
    try:
        return StreamingResponse(
            indic_voice_service.synthesize_professional_stream(
                request.text,
                voice_id=request.voice_id or "en_professional_male"
            ),
            media_type="audio/mpeg"
        )
    except Exception as e:
        logger.error(f"[API ERROR] TTS failed: {e}")
        raise HTTPException(status_code=500, detail="Speech synthesis failed")
