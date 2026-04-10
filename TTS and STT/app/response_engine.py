from __future__ import annotations

import re
from typing import Any


Tone = str


class TemplateResponseEngine:
    def __init__(self, voice_config: dict[str, Any]) -> None:
        self.voice_config = voice_config
        self.openers = voice_config.get("preferred_openers", [])

    def infer_tone(self, message: str) -> Tone:
        text = message.lower()

        if self._contains_any(
            text,
            [
                "error",
                "failed",
                "failure",
                "not able",
                "unable",
                "problem",
                "issue",
                "not working",
            ],
        ):
            return "error_handling"

        if self._contains_any(
            text,
            ["urgent", "immediate", "asap", "critical", "deadline", "important alert"],
        ):
            return "alert"

        if self._contains_any(text, ["how", "steps", "guide", "procedure", "process"]):
            return "instructional"

        if self._contains_any(text, ["thank you", "thanks", "that's all", "that is all"]):
            return "friendly"

        if self._contains_any(text, ["worried", "help me", "confused", "not sure"]):
            return "supportive"

        return "informational"

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _default_opener(self, tone: Tone) -> str:
        if tone == "instructional":
            return "You can follow these steps."
        if tone == "error_handling":
            return "I am sorry for the inconvenience."
        if tone == "alert":
            return "Please note this is important."
        if tone == "supportive":
            return "I understand, and I am here to help."
        if tone == "friendly":
            return "You are welcome."
        if self.openers:
            return self.openers[0]
        return "Sure, I will help you with that."

    @staticmethod
    def _build_instruction_steps(message: str) -> list[str]:
        cleaned = re.sub(r"[^\w\s]", "", message).strip()
        if not cleaned:
            return [
                "First, open the application.",
                "Then, go to the required section.",
                "Next, complete each field carefully.",
                "Finally, submit and confirm the update.",
            ]

        return [
            "First, open the relevant page in your application.",
            "Then, select the option that matches your request.",
            "Next, enter the details carefully and review once.",
            "Finally, submit the request and wait for confirmation.",
        ]

    def generate(self, message: str) -> tuple[str, Tone]:
        tone = self.infer_tone(message)

        if tone == "instructional":
            steps = self._build_instruction_steps(message)
            response = (
                f"{self._default_opener(tone)} "
                f"{steps[0]} {steps[1]} {steps[2]} {steps[3]} "
                "If you want, I can stay with you while you do this."
            )
            return response, tone

        if tone == "error_handling":
            response = (
                f"{self._default_opener(tone)} "
                "Let me check that for you. "
                "Please share the exact error message, and I will guide you step by step."
            )
            return response, tone

        if tone == "alert":
            response = (
                f"{self._default_opener(tone)} "
                "Please complete this action today to avoid interruption. "
                "I can help you finish it now."
            )
            return response, tone

        if tone == "supportive":
            response = (
                f"{self._default_opener(tone)} "
                "Please wait a moment while I check the best option for you. "
                "You are in the right place."
            )
            return response, tone

        if tone == "friendly":
            response = (
                f"{self._default_opener(tone)} "
                "Happy to help. "
                "If you need anything else, please let me know."
            )
            return response, tone

        response = (
            f"{self._default_opener(tone)} "
            "Let me check that for you. "
            "Please wait a moment while I prepare the correct information."
        )
        return response, tone
