from pydantic import BaseModel, Field
from typing import Optional

# Synthesis cost scales with input length, so cap it at the schema boundary.
# Roughly a long assistant reply; anything larger is a client bug or abuse.
MAX_TTS_TEXT_LENGTH = 5000


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TTS_TEXT_LENGTH)
    voice_id: Optional[str] = "en_professional_male"
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
