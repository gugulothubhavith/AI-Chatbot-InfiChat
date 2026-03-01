from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "en_professional_male"
    speed: Optional[float] = 1.0
