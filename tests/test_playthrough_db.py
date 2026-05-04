"""Tests for lib/playthrough_db/."""

from __future__ import annotations

import pathlib

import pytest

from playthrough_db import (
    delete_session,
    get_session,
    init_db,
    list_sessions,
    write_session,
)


@pytest.fixture()
def tmp_db(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "playthroughs.sqlite"


@pytest.fixture()
def example_session() -> dict:
    return {
        "session_id": "abc-123",
        "started_at": "2026-04-26T10:00:00Z",
        "ended_at": "2026-04-26T10:30:00Z",
        "status": "completed",
        "ending_type": "transmit",
        "final_score": 12,
        "final_o2": 70,
        "final_morale": 58,
        "player_kind": "human",
        "game_version": "v0.2.0-alpha",
        "notes": "first contact with Chen",
        "turns": [
            {
                "turn_number": 1,
                "command": "open locker",
                "response": "You open the emergency locker.",
                "o2": 99,
                "morale": 50,
                "current_room": "Crew Quarters",
                "inventory": [],
                "truth_states": {"corridor-pressurized": False},
            },
            {
                "turn_number": 2,
                "command": "take flashlight",
                "response": "Taken.",
                "o2": 98,
                "morale": 50,
                "current_room": "Crew Quarters",
                "inventory": ["flashlight"],
                "truth_states": {"corridor-pressurized": False},
            },
        ],
        "ai_calls": [
            {
                "turn_number": 2,
                "role": "station-ai",
                "model": "claude-sonnet-4-5",
                "prompt_hash": "deadbeef",
                "response": "Comrade.",
                "cost_usd": 0.0012,
                "input_tokens": 800,
                "output_tokens": 50,
            }
        ],
        "ship_state_log": [
            {
                "turn_number": 1,
                "snapshot_json": {
                    "mission": {"turn": 1},
                    "reactor": {"state": "idled"},
                },
            }
        ],
        "metadata": {"experiment": "wave-3 dispatch", "branch": "develop"},
    }


def test_init_db_creates_schema(tmp_db):
    path = init_db(tmp_db)
    assert path == tmp_db.expanduser()
    assert tmp_db.exists()


def test_init_db_idempotent(tmp_db):
    init_db(tmp_db)
    init_db(tmp_db)
    assert tmp_db.exists()


def test_write_and_get_session(tmp_db, example_session):
    counts = write_session(example_session, db_path=tmp_db)
    assert counts == {
        "sessions": 1,
        "turns": 2,
        "ai_calls": 1,
        "snapshots": 1,
        "metadata": 2,
    }

    out = get_session("abc-123", db_path=tmp_db)
    assert out is not None
    assert out["id"] == "abc-123"
    assert out["status"] == "completed"
    assert out["ending_type"] == "transmit"
    assert len(out["turns"]) == 2
    assert out["turns"][0]["command"] == "open locker"
    assert out["turns"][1]["inventory"] == ["flashlight"]
    assert len(out["ai_calls"]) == 1
    assert out["ai_calls"][0]["role"] == "station-ai"
    assert len(out["ship_state_log"]) == 1
    assert out["ship_state_log"][0]["snapshot_json"]["reactor"]["state"] == "idled"
    assert out["metadata"]["experiment"] == "wave-3 dispatch"


def test_get_session_returns_none_for_missing(tmp_db):
    assert get_session("does-not-exist", db_path=tmp_db) is None


def test_idempotent_rewrite_does_not_duplicate(tmp_db, example_session):
    write_session(example_session, db_path=tmp_db)
    write_session(example_session, db_path=tmp_db)
    out = get_session("abc-123", db_path=tmp_db)
    assert out is not None
    # Each list should still be the same length, not doubled.
    assert len(out["turns"]) == 2
    assert len(out["ai_calls"]) == 1
    assert len(out["ship_state_log"]) == 1
    assert len(out["metadata"]) == 2


def test_rewrite_replaces_child_rows(tmp_db, example_session):
    write_session(example_session, db_path=tmp_db)
    # Modify and rewrite
    modified = {**example_session}
    modified["turns"] = [example_session["turns"][0]]
    modified["ai_calls"] = []
    write_session(modified, db_path=tmp_db)
    out = get_session("abc-123", db_path=tmp_db)
    assert out is not None
    assert len(out["turns"]) == 1
    assert len(out["ai_calls"]) == 0


def test_list_sessions_orders_by_recency(tmp_db, example_session):
    a = {**example_session, "session_id": "a", "started_at": "2026-04-25T10:00:00Z"}
    b = {**example_session, "session_id": "b", "started_at": "2026-04-26T10:00:00Z"}
    c = {**example_session, "session_id": "c", "started_at": "2026-04-24T10:00:00Z"}
    for s in (a, b, c):
        write_session(s, db_path=tmp_db)

    sessions = list_sessions(db_path=tmp_db)
    assert [s["id"] for s in sessions] == ["b", "a", "c"]


def test_list_sessions_filters_by_player_kind(tmp_db, example_session):
    a = {**example_session, "session_id": "human-a", "player_kind": "human"}
    b = {**example_session, "session_id": "agent-b", "player_kind": "agent:claude-sonnet-4-5"}
    write_session(a, db_path=tmp_db)
    write_session(b, db_path=tmp_db)

    humans = list_sessions(player_kind="human", db_path=tmp_db)
    assert {s["id"] for s in humans} == {"human-a"}

    agents = list_sessions(
        player_kind="agent:claude-sonnet-4-5", db_path=tmp_db
    )
    assert {s["id"] for s in agents} == {"agent-b"}


def test_list_sessions_filters_by_ending(tmp_db, example_session):
    a = {**example_session, "session_id": "transmit-a", "ending_type": "transmit"}
    b = {**example_session, "session_id": "suffocate-b", "ending_type": "suffocate"}
    write_session(a, db_path=tmp_db)
    write_session(b, db_path=tmp_db)

    transmits = list_sessions(ending_type="transmit", db_path=tmp_db)
    assert {s["id"] for s in transmits} == {"transmit-a"}


def test_list_sessions_filters_by_since(tmp_db, example_session):
    a = {**example_session, "session_id": "old", "started_at": "2025-01-01T00:00:00Z"}
    b = {**example_session, "session_id": "new", "started_at": "2026-04-26T10:00:00Z"}
    write_session(a, db_path=tmp_db)
    write_session(b, db_path=tmp_db)

    recent = list_sessions(since="2026-01-01T00:00:00Z", db_path=tmp_db)
    assert {s["id"] for s in recent} == {"new"}


def test_list_sessions_respects_limit(tmp_db, example_session):
    for i in range(5):
        write_session(
            {
                **example_session,
                "session_id": f"s-{i}",
                "started_at": f"2026-04-{20 + i}T10:00:00Z",
            },
            db_path=tmp_db,
        )
    rows = list_sessions(limit=3, db_path=tmp_db)
    assert len(rows) == 3


def test_delete_session_cascades(tmp_db, example_session):
    write_session(example_session, db_path=tmp_db)
    removed = delete_session("abc-123", db_path=tmp_db)
    assert removed is True
    assert get_session("abc-123", db_path=tmp_db) is None
    # Children gone too
    sessions = list_sessions(db_path=tmp_db)
    assert sessions == []


def test_delete_missing_session_returns_false(tmp_db):
    assert delete_session("does-not-exist", db_path=tmp_db) is False


def test_write_session_requires_session_id(tmp_db):
    with pytest.raises(ValueError):
        write_session({"started_at": "2026-04-26T10:00:00Z"}, db_path=tmp_db)


def test_write_session_handles_missing_optional_fields(tmp_db):
    minimal = {
        "session_id": "minimal-1",
        "started_at": "2026-04-26T10:00:00Z",
        "status": "in_progress",
    }
    counts = write_session(minimal, db_path=tmp_db)
    assert counts["sessions"] == 1
    assert counts["turns"] == 0
    out = get_session("minimal-1", db_path=tmp_db)
    assert out is not None
    assert out["status"] == "in_progress"
    assert out["turns"] == []


def test_env_var_db_path(tmp_path, example_session, monkeypatch):
    custom = tmp_path / "custom.sqlite"
    monkeypatch.setenv("MIRSEND_DB_PATH", str(custom))
    write_session(example_session)
    assert custom.exists()
