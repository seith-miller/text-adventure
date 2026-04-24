"""Voice-kit loader for Mir's End.

Reads and caches the writing-sample and persona markdown files that define
the narrative voice for each LLM role.
"""

from __future__ import annotations

import os
from pathlib import Path

# Resolve project root relative to this file: lib/mirs_end_bridge/voice_kit.py
# Project root is two levels up from lib/mirs_end_bridge/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_VOICE_FILES = {
    "darkling_beetles": "docs/writing-samples/darkling-beetles.md",
    "the_man_ava": "docs/writing-samples/the-man-ava.md",
    "writing_style": "docs/writing-style.md",
}

_STATION_AI_FILE = "docs/station-ai-persona.md"

# Module-level cache (populated on first call per role).
_cache: dict[str, dict[str, str]] = {}


def _read_file(relative_path: str) -> str:
    """Read a project-relative file and return its contents."""
    full_path = _PROJECT_ROOT / relative_path
    return full_path.read_text(encoding="utf-8")


def get_voice_kit(role: str) -> dict[str, str]:
    """Return the voice-kit dict for *role*, loading and caching on first call.

    Every role gets the three core voice files. The ``"station-ai"`` role
    additionally includes ``docs/station-ai-persona.md``.

    Returns a dict mapping short keys to the file contents::

        {
            "darkling_beetles": "...",
            "the_man_ava": "...",
            "writing_style": "...",
            "station_ai_persona": "...",   # station-ai role only
        }
    """
    if role in _cache:
        return _cache[role]

    kit: dict[str, str] = {}
    for key, rel_path in _VOICE_FILES.items():
        kit[key] = _read_file(rel_path)

    if role == "station-ai":
        kit["station_ai_persona"] = _read_file(_STATION_AI_FILE)

    _cache[role] = kit
    return kit


def clear_cache() -> None:
    """Clear the voice-kit cache (useful for testing)."""
    _cache.clear()
