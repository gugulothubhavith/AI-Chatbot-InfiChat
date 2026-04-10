from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AgentConfig:
    system_prompt: str
    voice_config: dict[str, Any]
    sample_dialogues: str


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8").strip()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def load_agent_config(
    root: Path | None = None,
    system_prompt_file: str = "system_prompt.txt",
    voice_config_file: str = "voice_config.json",
    sample_dialogues_file: str = "sample_dialogues.md",
) -> AgentConfig:
    base = root or PROJECT_ROOT
    return AgentConfig(
        system_prompt=_read_text(base / system_prompt_file),
        voice_config=_read_json(base / voice_config_file),
        sample_dialogues=_read_text(base / sample_dialogues_file),
    )
