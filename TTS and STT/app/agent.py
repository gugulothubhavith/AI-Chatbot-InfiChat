from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import AgentConfig, load_agent_config
from .models import ChatResponse, ChatTurn
from .response_engine import TemplateResponseEngine
from .tts_formatter import TTSFormatter


@dataclass
class AgentState:
    turns: list[ChatTurn]


class IndianVoiceAgent:
    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or load_agent_config()
        self.engine = TemplateResponseEngine(self.config.voice_config)
        self.formatter = TTSFormatter(self.config.voice_config)

    def respond(self, message: str, history: list[ChatTurn] | None = None) -> ChatResponse:
        _ = history or []
        draft, tone = self.engine.generate(message)
        reply = self.formatter.format(draft)
        profile_name = str(self.config.voice_config.get("profile_name", "default_profile"))
        language = str(self.config.voice_config.get("language", "en-IN"))
        accent = str(self.config.voice_config.get("accent", "neutral_indian_english"))
        return ChatResponse(
            reply=reply,
            tone=tone,
            profile_name=profile_name,
            language=language,
            accent=accent,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "profile_name": self.config.voice_config.get("profile_name"),
            "language": self.config.voice_config.get("language"),
            "accent": self.config.voice_config.get("accent"),
            "response_framework": self.config.voice_config.get("response_framework", []),
        }
