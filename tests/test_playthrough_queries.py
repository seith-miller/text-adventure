"""Tests for the m12 aggregation queries over the playthrough DB."""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from lib.playthrough_db import (  # noqa: E402
    commands_attempted,
    ending_distribution,
    fastest_path_to_ending,
    init_db,
    session_summaries,
    stuck_moments,
    stuck_moments_for_session,
    turns_to_first_argon_call,
    unrecognized_commands,
    write_session,
)


@pytest.fixture
def db(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "test.sqlite"
    init_db(p)
    return p


def _session(
    sid: str,
    *,
    player_kind: str = "agent:claude-sonnet-4-5",
    status: str = "completed",
    ending_type: str | None = "transmit",
    started_at: str = "2026-04-26T12:00:00+00:00",
    turns: list[dict] | None = None,
    metadata: dict[str, str] | None = None,
) -> dict:
    return {
        "session_id": sid,
        "started_at": started_at,
        "ended_at": "2026-04-26T12:30:00+00:00",
        "status": status,
        "ending_type": ending_type,
        "player_kind": player_kind,
        "game_version": "develop",
        "turns": turns or [],
        "metadata": metadata or {},
    }


def test_commands_attempted_aggregates_across_sessions(db):
    write_session(_session("s1", turns=[
        {"turn_number": 1, "command": "look", "response": "You see..."},
        {"turn_number": 2, "command": "open locker", "response": "Open."},
    ]), db_path=db)
    write_session(_session("s2", turns=[
        {"turn_number": 1, "command": "look", "response": "You see..."},
        {"turn_number": 2, "command": "pull lever", "response": "Click."},
    ]), db_path=db)

    counter = commands_attempted(db_path=db)
    assert counter["look"] == 2
    assert counter["open locker"] == 1
    assert counter["pull lever"] == 1


def test_commands_attempted_filters_by_player_kind(db):
    write_session(_session("a", player_kind="agent:m1", turns=[
        {"turn_number": 1, "command": "look", "response": ""},
    ]), db_path=db)
    write_session(_session("b", player_kind="human", turns=[
        {"turn_number": 1, "command": "look", "response": ""},
        {"turn_number": 2, "command": "wait", "response": ""},
    ]), db_path=db)

    counter = commands_attempted(player_kind="agent:m1", db_path=db)
    assert counter["look"] == 1
    assert "wait" not in counter


def test_unrecognized_commands_matches_inform_responses(db):
    write_session(_session("s1", turns=[
        {"turn_number": 1, "command": "open hatch",
         "response": "I beg your pardon."},
        {"turn_number": 2, "command": "look",
         "response": "You see a door."},
        {"turn_number": 3, "command": "use radio",
         "response": "That's not a verb I recognise."},
        {"turn_number": 4, "command": "open hatch",
         "response": "You can't see any such thing."},
    ]), db_path=db)

    counter = unrecognized_commands(db_path=db)
    assert counter["open hatch"] == 2
    assert counter["use radio"] == 1
    assert "look" not in counter


def test_ending_distribution_counts_by_type(db):
    write_session(_session("s1", ending_type="transmit", status="completed"), db_path=db)
    write_session(_session("s2", ending_type="transmit", status="completed"), db_path=db)
    write_session(_session("s3", ending_type="suffocate", status="completed"), db_path=db)
    write_session(_session("s4", ending_type=None, status="stuck"), db_path=db)

    dist = ending_distribution(db_path=db)
    assert dist["transmit"] == 2
    assert dist["suffocate"] == 1
    assert dist["stuck"] == 1  # falls back to status when ending_type is null


def test_stuck_moments_aggregates_rooms(db):
    metadata_a = {
        "stuck_moments": json.dumps([
            {"turn_start": 5, "turn_end": 14, "room": "Crew Quarters", "window": 10}
        ])
    }
    metadata_b = {
        "stuck_moments": json.dumps([
            {"turn_start": 8, "turn_end": 17, "room": "Crew Quarters", "window": 10}
        ])
    }
    metadata_c = {
        "stuck_moments": json.dumps([
            {"turn_start": 3, "turn_end": 12, "room": "Cupola", "window": 10}
        ])
    }
    write_session(_session("a", metadata=metadata_a), db_path=db)
    write_session(_session("b", metadata=metadata_b), db_path=db)
    write_session(_session("c", metadata=metadata_c), db_path=db)
    write_session(_session("d"), db_path=db)  # no stuck

    rooms = stuck_moments(db_path=db)
    assert rooms["Crew Quarters"] == 2
    assert rooms["Cupola"] == 1


def test_stuck_moments_for_session_returns_entries(db):
    entries = [{"turn_start": 5, "turn_end": 14, "room": "Crew Quarters", "window": 10}]
    write_session(
        _session("a", metadata={"stuck_moments": json.dumps(entries)}),
        db_path=db,
    )
    assert stuck_moments_for_session("a", db_path=db) == entries


def test_stuck_moments_for_session_empty_when_absent(db):
    write_session(_session("a"), db_path=db)
    assert stuck_moments_for_session("a", db_path=db) == []


def test_session_summaries_totals_cost(db):
    write_session(
        _session("a", metadata={"estimated_cost_usd": "0.42"}),
        db_path=db,
    )
    write_session(
        _session("b", status="stuck", ending_type=None,
                 metadata={"estimated_cost_usd": "0.18"}),
        db_path=db,
    )
    summary = session_summaries(db_path=db)
    assert summary["total"] == 2
    assert summary["by_status"]["completed"] == 1
    assert summary["by_status"]["stuck"] == 1
    assert summary["total_cost_usd"] == pytest.approx(0.6)


def test_turns_to_first_argon_call(db):
    write_session(_session("a", turns=[
        {"turn_number": 1, "command": "look", "response": ""},
        {"turn_number": 2, "command": "talk to argon", "response": ""},
        {"turn_number": 3, "command": "ask argon about lever", "response": ""},
    ]), db_path=db)
    write_session(_session("b", turns=[
        {"turn_number": 1, "command": "north", "response": ""},
        {"turn_number": 2, "command": "wait", "response": ""},
    ]), db_path=db)
    write_session(_session("c", turns=[
        {"turn_number": 1, "command": "talk to station ai", "response": ""},
    ]), db_path=db)

    turns = turns_to_first_argon_call(db_path=db)
    assert turns == [1, 2]


def test_fastest_path_to_ending_picks_shortest(db):
    write_session(_session("long", ending_type="transmit", turns=[
        {"turn_number": i, "command": f"step{i}", "response": ""} for i in range(1, 21)
    ]), db_path=db)
    write_session(_session("short", ending_type="transmit", turns=[
        {"turn_number": i, "command": f"step{i}", "response": ""} for i in range(1, 6)
    ]), db_path=db)
    write_session(_session("other", ending_type="suffocate", turns=[
        {"turn_number": i, "command": f"die{i}", "response": ""} for i in range(1, 4)
    ]), db_path=db)

    out = fastest_path_to_ending("transmit", db_path=db)
    assert out is not None
    assert out["session_id"] == "short"
    assert out["turn_count"] == 5
    assert out["command_path"] == ["step1", "step2", "step3", "step4", "step5"]


def test_fastest_path_returns_none_for_missing_ending(db):
    write_session(_session("a", ending_type="transmit"), db_path=db)
    assert fastest_path_to_ending("nonexistent_ending", db_path=db) is None


def test_filters_by_since_date(db):
    write_session(
        _session("old", started_at="2026-01-01T00:00:00+00:00"),
        db_path=db,
    )
    write_session(
        _session("new", started_at="2026-04-26T00:00:00+00:00"),
        db_path=db,
    )
    summary = session_summaries(since="2026-04-01T00:00:00+00:00", db_path=db)
    assert summary["total"] == 1
