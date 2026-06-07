"""Transcript logger for Mir's End LLM bridge.

Every Claude call is logged as a JSON-lines entry with timestamp, role,
prompt, response, token counts, and estimated cost. Append-only to
``logs/llm-calls/YYYY-MM-DD.jsonl``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .types import Prompt

# Resolve project root relative to this file.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs" / "llm-calls"

# Allow overriding the log directory for testing.
_log_dir_override: Path | None = None


def set_log_dir(path: Path | None) -> None:
    """Override the log directory (set to ``None`` to restore default)."""
    global _log_dir_override
    _log_dir_override = path


def _get_log_dir() -> Path:
    return _log_dir_override if _log_dir_override is not None else _LOG_DIR


def log_call(
    *,
    role: str,
    prompt: Prompt,
    response_text: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    model: str,
) -> Path:
    """Append a single log entry and return the log file path.

    Creates the log directory if it does not exist.
    """
    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    log_file = log_dir / f"{now.strftime('%Y-%m-%d')}.jsonl"

    entry = {
        "timestamp": now.isoformat(),
        "role": role,
        "model": model,
        "prompt_system_length": len(prompt.get("system", "")),
        "prompt_messages_count": len(prompt.get("messages", [])),
        "prompt_system_preview": prompt.get("system", "")[:200],
        "response_text": response_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    return log_file
