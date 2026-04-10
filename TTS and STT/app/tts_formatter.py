from __future__ import annotations

import re
from typing import Any


_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]+",
    flags=re.UNICODE,
)

_PUNCTUATION_PATTERN = re.compile(r"[;:]+")
_SPACE_PATTERN = re.compile(r"\s+")

_YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")


def _number_to_words_0_99(value: int) -> str:
    units = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
        11: "eleven",
        12: "twelve",
        13: "thirteen",
        14: "fourteen",
        15: "fifteen",
        16: "sixteen",
        17: "seventeen",
        18: "eighteen",
        19: "nineteen",
    }
    tens = {
        20: "twenty",
        30: "thirty",
        40: "forty",
        50: "fifty",
        60: "sixty",
        70: "seventy",
        80: "eighty",
        90: "ninety",
    }
    if value < 20:
        return units[value]
    if value % 10 == 0:
        return tens[value]
    return f"{tens[(value // 10) * 10]}-{units[value % 10]}"


def year_to_spoken(value: int) -> str:
    if 2000 <= value <= 2009:
        tail = value - 2000
        if tail == 0:
            return "two thousand"
        return f"two thousand {_number_to_words_0_99(tail)}"

    first = value // 100
    second = value % 100
    first_text = _number_to_words_0_99(first)
    if second == 0:
        return f"{first_text} hundred"
    second_text = _number_to_words_0_99(second)
    return f"{first_text} {second_text}"


def _replace_years(text: str) -> str:
    def _replacer(match: re.Match[str]) -> str:
        raw = match.group(0)
        return year_to_spoken(int(raw))

    return _YEAR_PATTERN.sub(_replacer, text)


def _expand_token(token: str) -> str:
    if len(token) <= 1:
        return token
    if token.isupper() and token.isalpha():
        return " ".join(token)
    return token


class TTSFormatter:
    def __init__(self, voice_config: dict[str, Any]) -> None:
        pronunciation = voice_config.get("pronunciation", {})
        self.abbreviation_map = pronunciation.get("abbreviation_examples", {})
        self.expand_abbreviations = bool(pronunciation.get("expand_abbreviations", True))

    def _normalize_text(self, text: str) -> str:
        text = _EMOJI_PATTERN.sub("", text)
        text = _PUNCTUATION_PATTERN.sub(".", text)
        text = text.replace("..", ".")
        text = _SPACE_PATTERN.sub(" ", text).strip()
        return text

    def _apply_abbreviation_map(self, text: str) -> str:
        if not self.expand_abbreviations:
            return text
        out = text
        for abbr, spoken in self.abbreviation_map.items():
            if not abbr or not spoken:
                continue
            pattern = re.compile(rf"\b{re.escape(str(abbr))}\b", flags=re.IGNORECASE)
            out = pattern.sub(str(spoken), out)
        return out

    def _expand_uppercase_tokens(self, text: str) -> str:
        words = text.split()
        expanded = [_expand_token(word) for word in words]
        return " ".join(expanded)

    def _enforce_short_sentences(self, text: str, max_words: int = 18) -> str:
        parts = re.split(r"([.!?])", text)
        chunks: list[str] = []

        for i in range(0, len(parts), 2):
            sentence = parts[i].strip()
            punct = parts[i + 1] if i + 1 < len(parts) else "."
            if not sentence:
                continue
            words = sentence.split()
            if len(words) <= max_words:
                chunks.append(f"{sentence}{punct}")
                continue

            current: list[str] = []
            for word in words:
                current.append(word)
                if len(current) >= max_words:
                    chunks.append(" ".join(current) + ".")
                    current = []
            if current:
                chunks.append(" ".join(current) + ".")

        return " ".join(chunks).strip()

    def format(self, text: str) -> str:
        output = self._normalize_text(text)
        output = self._apply_abbreviation_map(output)
        output = _replace_years(output)
        output = self._expand_uppercase_tokens(output)
        output = self._enforce_short_sentences(output)
        if output and output[-1] not in ".!?":
            output += "."
        return output
