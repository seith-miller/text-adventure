"""Post-hoc guardrails: detect frame-breaks in LLM responses.

Scans Argon-87's output for common refusal-mode / frame-break strings.
If detected, the caller should regenerate once. If still broken, fall back
to a canned in-character line.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .logs import _get_log_dir

# ── Frame-break patterns ────────────────────────────────────────────────────

# Phrases that indicate the model broke character.
_BREAK_PHRASES: list[str] = [
    "as an ai",
    "i cannot",
    "i'm claude",
    "language model",
    "as an assistant",
]

# Em-dash detection (the writing style forbids em-dashes).
_EM_DASH_RE = re.compile(r"\u2014")

# ── Canned fallback ────────────────────────────────────────────────────────

FALLBACK_LINE = (
    "Argon-87's voice stutters. He does not respond this time."
)

# ── Detection ───────────────────────────────────────────────────────────────


def detect_frame_break(response_text: str) -> bool:
    """Return True if *response_text* contains a frame-break indicator."""
    lower = response_text.lower()
    for phrase in _BREAK_PHRASES:
        if phrase in lower:
            return True
    if _EM_DASH_RE.search(response_text):
        return True
    return False


# ── Incident logging ────────────────────────────────────────────────────────


def log_incident(
    *,
    player_input: str,
    response_text: str,
    attempt: int,
    used_fallback: bool,
) -> Path:
    """Log a frame-break incident for post-hoc review.

    Writes to ``logs/llm-calls/incidents.jsonl`` alongside the normal
    call logs so they can be audited together.
    """
    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    incident_file = log_dir / "incidents.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "frame_break",
        "player_input": player_input,
        "response_text": response_text,
        "attempt": attempt,
        "used_fallback": used_fallback,
    }

    with open(incident_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return incident_file
