import re
import logging
import time
import asyncio
import numpy as np
from typing import AsyncGenerator
import os

logger = logging.getLogger(__name__)

class IndicNormalizer:
    """Professional Indian Text Normalization Engine."""
    
    def __init__(self):
        self.currency_pattern = re.compile(r"₹\s?(\d+(?:,\d+)*)")
        self.units_map = {
            "Lakh": 100000,
            "Crore": 10000000,
            "k": 1000
        }
        self.abbreviations = {
            "KYC": "K Y C",
            "OTP": "O T P",
            "API": "A P I",
            "AI": "Artificial Intelligence",
            "Rs.": "Rupees",
            "INR": "Indian Rupees"
        }

    def _format_indian_number(self, amount: int) -> str:
        """Convert numbers to Lakhs/Crores spoken format."""
        if amount >= 10000000:
            crores = amount / 10000000
            if crores == int(crores): return f"{int(crores)} Crore"
            return f"{crores:.2f} Crore"
        elif amount >= 100000:
            lakhs = amount / 100000
            if lakhs == int(lakhs): return f"{int(lakhs)} Lakh"
            return f"{lakhs:.2f} Lakh"
        return str(amount)

    def normalize(self, text: str) -> str:
        # 1. Handle Currency (₹5,00,000 -> 5 Lakh Rupees)
        for match in self.currency_pattern.finditer(text):
            raw_val = match.group(1).replace(",", "")
            try:
                val = int(raw_val)
                spoken = f"{self._format_indian_number(val)} Rupees"
                text = text.replace(match.group(0), spoken)
            except: pass

        # 2. Expand Business Abbreviations
        for abbr, spoken in self.abbreviations.items():
            text = re.sub(rf"\b{re.escape(abbr)}\b", spoken, text)

        # 3. Clean up formatting
        text = text.replace("*", "").replace("#", "").strip()
        return text

class IndicVoiceService:
    def __init__(self):
        self.normalizer = IndicNormalizer()
        self.voice_map = {
            "en_professional_male": "en-IN-PrabhatNeural",
            "en_professional_female": "en-IN-NeerjaNeural",
            "hi_corporate_female": "hi-IN-SwaraNeural",
            "hi_corporate_male": "hi-IN-MadhurNeural",
            "te_empathetic_male": "te-IN-MohanNeural",
            "te_empathetic_female": "te-IN-ShrutiNeural",
            "hi_alert_female": "hi-IN-SwaraNeural"
        }
        logger.info("IndicVoiceService initialized with Edge-TTS professional engine (MP3 Streaming).")

    async def synthesize_professional_stream(self, text: str, voice_id: str = "en_professional_male") -> AsyncGenerator[bytes, None]:
        """Highly advanced professional synthesis using high-fidelity edge-tts (MP3 format)."""
        import edge_tts
        
        normalized_text = self.normalizer.normalize(text)
        actual_voice = self.voice_map.get(voice_id, "en-IN-NeerjaNeural")
        
        rate = "+0%"
        if "alert" in voice_id:
            rate = "+25%"
        elif "empathetic" in voice_id:
            rate = "-10%"

        logger.info(f"[PROFESSIONAL TTS] Engine: Edge-TTS | Voice: {actual_voice} | Format: MP3")
        
        communicate = edge_tts.Communicate(normalized_text, actual_voice, rate=rate)
        
        t_start = time.time()
        is_first = True
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                if is_first:
                    is_first = False
                    logger.info(f"[TTS TIMING] MP3 Stream Start: {(time.time() - t_start)*1000:.1f}ms")
                yield chunk["data"]

indic_voice_service = IndicVoiceService()
