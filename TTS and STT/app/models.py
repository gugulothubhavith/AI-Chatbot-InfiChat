from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatTurn:
    role: str
    text: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChatTurn":
        role = str(payload.get("role", "")).strip().lower()
        text = str(payload.get("text", "")).strip()
        if role not in {"user", "assistant", "system"}:
            raise ValueError("turn.role must be one of: user, assistant, system")
        if not text:
            raise ValueError("turn.text cannot be empty")
        return cls(role=role, text=text)


@dataclass
class ChatRequest:
    message: str
    history: list[ChatTurn] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ChatRequest":
        message = str(payload.get("message", "")).strip()
        if not message:
            raise ValueError("message is required")

        raw_history = payload.get("history", [])
        history: list[ChatTurn] = []
        if isinstance(raw_history, list):
            for item in raw_history:
                if isinstance(item, dict):
                    history.append(ChatTurn.from_dict(item))
        else:
            raise ValueError("history must be a list")

        return cls(message=message, history=history)


@dataclass
class ChatResponse:
    reply: str
    tone: str
    profile_name: str
    language: str
    accent: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "reply": self.reply,
            "tone": self.tone,
            "profile_name": self.profile_name,
            "language": self.language,
            "accent": self.accent,
        }
