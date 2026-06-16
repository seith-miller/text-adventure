"""Tests for `lib.playthrough_db.normalize_session_payload`.

The normalizer is the single translation layer between every payload
shape the project sends (browser ui.js, scripts/playtest.py,
scripts/playtest-pool.py, scripts/import_mcp_sessions.py) and the
`write_session` schema. If this drifts, ingest forks silently.
"""

from __future__ import annotations

import pytest

from lib.playthrough_db import normalize_session_payload


# ── shape: browser ui.js ─────────────────────────────────────────────


def test_browser_shape_turns_as_count_becomes_list_of_dicts():
    """ui.js sends `turns: <int>` plus `command_history: [...]`."""
    body = {
        "session_id": "browser-1",
        "turns": 3,
        "command_history": ["look", "open locker", "take all"],
        "final_state": {"score": 7, "o2": 84, "morale": 62},
    }
    payload = normalize_session_payload(body)
    assert payload["session_id"] == "browser-1"
    assert isinstance(payload["turns"], list)
    assert len(payload["turns"]) == 3
    assert payload["turns"][0] == {
        "turn_number": 1,
        "command": "look",
        "response": None,
    }
    # final_state fields lift to scalar columns.
    assert payload["final_score"] == 7
    assert payload["final_o2"] == 84
    assert payload["final_morale"] == 62


# ── shape: playtest.py --output ─────────────────────────────────────


def test_playtest_shape_flat_finals_used_directly():
    """playtest.py writes final_* as scalars, no nested final_state."""
    body = {
        "session_id": "playtest-1",
        "started_at": "2026-06-08T00:00:00Z",
        "ended_at": "2026-06-08T00:05:00Z",
        "status": "completed",
        "ending_type": "transmit",
        "final_score": 11,
        "final_o2": 50,
        "final_morale": 80,
        "player_kind": "agent:claude-opus-4-7",
        "game_version": "v0.3.0",
        "command_history": ["n", "x console", "transmit"],
        "transcript": "...",
    }
    payload = normalize_session_payload(body)
    assert payload["final_score"] == 11
    assert payload["final_o2"] == 50
    assert payload["final_morale"] == 80
    assert payload["status"] == "completed"
    assert payload["ending_type"] == "transmit"
    assert payload["player_kind"] == "agent:claude-opus-4-7"
    assert payload["game_version"] == "v0.3.0"
    # Three commands → three structured turn dicts.
    assert len(payload["turns"]) == 3
    assert [t["command"] for t in payload["turns"]] == ["n", "x console", "transmit"]


# ── shape: pool worker (turns already structured) ───────────────────


def test_pool_shape_passes_turns_list_through_unchanged():
    """The pool worker sends fully-structured turn dicts; do not rebuild them."""
    structured_turns = [
        {
            "turn_number": 1,
            "command": "look",
            "response": "You are in Crew Quarters.",
            "o2": 100,
            "morale": 70,
        },
        {
            "turn_number": 2,
            "command": "open locker",
            "response": "You open the emergency locker.",
            "o2": 99,
            "morale": 70,
        },
    ]
    body = {
        "session_id": "pool-1",
        "turns": structured_turns,
    }
    payload = normalize_session_payload(body)
    assert payload["turns"] is structured_turns
    # Pre-structured per-turn responses must survive.
    assert payload["turns"][0]["response"] == "You are in Crew Quarters."


# ── validation ──────────────────────────────────────────────────────


def test_missing_session_id_raises_valueerror():
    with pytest.raises(ValueError, match="session_id is required"):
        normalize_session_payload({})


def test_empty_session_id_raises_valueerror():
    with pytest.raises(ValueError, match="session_id is required"):
        normalize_session_payload({"session_id": ""})


def test_non_string_session_id_raises_valueerror():
    with pytest.raises(ValueError, match="session_id is required"):
        normalize_session_payload({"session_id": 42})


# ── defaults ────────────────────────────────────────────────────────


def test_missing_optional_fields_get_safe_defaults():
    payload = normalize_session_payload({"session_id": "x"})
    assert payload["status"] == "in_progress"
    assert payload["player_kind"] == "unknown"
    assert payload["game_version"] == "unknown"
    assert payload["turns"] == []
    assert payload["metadata"] == {}
    assert payload["final_score"] is None
    assert payload["final_o2"] is None
    assert payload["final_morale"] is None


def test_flat_finals_win_over_nested_when_both_present():
    """If `final_score` is set directly, do not fall back to `final_state.score`."""
    body = {
        "session_id": "x",
        "final_score": 100,
        "final_state": {"score": 5},
    }
    payload = normalize_session_payload(body)
    assert payload["final_score"] == 100


def test_nested_finals_used_only_when_flat_missing():
    body = {
        "session_id": "x",
        "final_state": {"score": 5, "o2": 12},
    }
    payload = normalize_session_payload(body)
    assert payload["final_score"] == 5
    assert payload["final_o2"] == 12
