"""
Translate the various session-payload shapes the project sends into the
schema `write_session` expects.

Callers send to `/v1/sessions` (or directly to `write_session` via a
CLI bridge) in different shapes:

  - browser ui.js: `turns` is an int (count), `final_state` is a dict,
    `command_history` is a list of strings, `transcript` is a joined
    string
  - scripts/playtest.py: flat `final_o2` / `final_morale` / `final_score`,
    `command_history` list of strings, `transcript` joined string
  - scripts/playtest-pool.py worker: `turns` is already a list of full
    per-turn dicts
  - scripts/import_mcp_sessions.py: imports playtest.py-shaped JSON
    files from disk

All paths share `session_id`, `started_at`, `status`, etc. This module
is the single normalization point; bypass it and the schema will drift.
"""

from __future__ import annotations

from typing import Any


def normalize_session_payload(body: dict) -> dict:
    """Translate any accepted payload shape into the `write_session` schema.

    Raises `ValueError` if `session_id` is missing or not a non-empty string.
    """
    sid = body.get("session_id")
    if not isinstance(sid, str) or not sid:
        raise ValueError("session_id is required and must be a non-empty string")

    turns_in = body.get("turns")
    if isinstance(turns_in, list):
        turns = turns_in
    else:
        turns = []
        for i, cmd in enumerate(body.get("command_history") or [], start=1):
            turns.append({"turn_number": i, "command": cmd, "response": None})

    fs = body.get("final_state") or {}

    def _pick(*keys: str, default: Any = None) -> Any:
        for k in keys:
            if k in body and body[k] is not None:
                return body[k]
        return default

    return {
        "session_id": sid,
        "started_at": body.get("started_at"),
        "ended_at": body.get("ended_at"),
        "status": body.get("status", "in_progress"),
        "ending_type": body.get("ending_type"),
        "final_score": _pick("final_score", default=fs.get("score")),
        "final_o2": _pick("final_o2", default=fs.get("o2")),
        "final_morale": _pick("final_morale", default=fs.get("morale")),
        "player_kind": body.get("player_kind", "unknown"),
        "game_version": body.get("game_version", "unknown"),
        "notes": body.get("notes"),
        "turns": turns,
        "metadata": body.get("metadata") or {},
    }
