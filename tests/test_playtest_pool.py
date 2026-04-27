"""Tests for the m12 pool runner: ingest helper + report formatter."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _load_pool_module():
    """The pool script has a hyphen in its name, so importlib it."""
    spec = importlib.util.spec_from_file_location(
        "playtest_pool",
        str(REPO_ROOT / "scripts" / "playtest-pool.py"),
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pool = _load_pool_module()


def _driver_summary(session_id="abc", **overrides) -> dict:
    base = {
        "session_id": session_id,
        "started_at": "2026-04-26T12:00:00+00:00",
        "ended_at": "2026-04-26T12:30:00+00:00",
        "model": "claude-sonnet-4-5",
        "status": "completed",
        "ending_type": "transmit",
        "final_score": 14,
        "final_o2": 80,
        "final_morale": 72,
        "input_tokens": 1000,
        "output_tokens": 200,
        "estimated_cost_usd": 0.0033,
        "command_history": ["look", "open locker"],
        "transcript": "...",
        "turns_count": 2,
        "bailout_reason": "ending",
        "turns": [
            {"turn_number": 1, "command": "look", "response": "You see..."},
            {"turn_number": 2, "command": "open locker", "response": "Opens."},
        ],
        "stuck_moments": [],
        "metadata": {
            "bailout_reason": "ending",
            "estimated_cost_usd": "0.0033",
            "model": "claude-sonnet-4-5",
        },
        "player_kind": "agent:claude-sonnet-4-5",
        "game_version": "develop",
    }
    base.update(overrides)
    return base


def test_ingest_summary_writes_session(tmp_path):
    db = tmp_path / "ingest.sqlite"
    summary = _driver_summary()
    assert pool._ingest_summary(summary, db_path=db) is True

    from lib.playthrough_db import get_session  # noqa: PLC0415
    row = get_session("abc", db_path=db)
    assert row is not None
    assert row["status"] == "completed"
    assert row["ending_type"] == "transmit"
    assert row["player_kind"] == "agent:claude-sonnet-4-5"
    assert len(row["turns"]) == 2


def test_ingest_summary_skips_errors(tmp_path):
    db = tmp_path / "skip.sqlite"
    assert pool._ingest_summary({"error": "timeout"}, db_path=db) is False


def test_render_report_with_empty_db(tmp_path):
    db = tmp_path / "empty.sqlite"
    from lib.playthrough_db import init_db  # noqa: PLC0415
    init_db(db)
    report = pool.render_report(db_path=db)
    assert "# Playtest pool report" in report
    assert "Runs: 0" in report
    assert "(none)" in report or "(no" in report


def test_render_report_with_data(tmp_path):
    db = tmp_path / "data.sqlite"
    from lib.playthrough_db import write_session  # noqa: PLC0415

    completed = {
        "session_id": "ok-1",
        "started_at": "2026-04-26T12:00:00+00:00",
        "ended_at": "2026-04-26T12:30:00+00:00",
        "status": "completed",
        "ending_type": "transmit",
        "player_kind": "agent:claude-sonnet-4-5",
        "game_version": "develop",
        "turns": [
            {"turn_number": 1, "command": "look", "response": "You see..."},
            {"turn_number": 2, "command": "open hatch",
             "response": "I beg your pardon."},
            {"turn_number": 3, "command": "talk to argon",
             "response": "Argon-87 here."},
            {"turn_number": 4, "command": "transmit",
             "response": "*** Begin preparations ***"},
        ],
        "metadata": {"estimated_cost_usd": "0.42"},
    }
    stuck = {
        "session_id": "stuck-1",
        "started_at": "2026-04-26T12:00:00+00:00",
        "ended_at": "2026-04-26T13:00:00+00:00",
        "status": "stuck",
        "ending_type": None,
        "player_kind": "agent:claude-sonnet-4-5",
        "game_version": "develop",
        "turns": [
            {"turn_number": 1, "command": "look", "response": "You see..."},
        ],
        "metadata": {
            "estimated_cost_usd": "0.10",
            "stuck_moments": json.dumps([
                {"turn_start": 5, "turn_end": 14,
                 "room": "Crew Quarters", "window": 10}
            ]),
        },
    }
    write_session(completed, db_path=db)
    write_session(stuck, db_path=db)

    report = pool.render_report(db_path=db)
    assert "Runs: 2" in report
    assert "Completed (reached ending): 1" in report
    assert "Stuck-loop bailouts: 1" in report
    assert "Total cost: $0.52" in report
    assert "transmit: 1" in report
    assert "Crew Quarters: 1" in report
    assert "'open hatch'" in report  # unrecognized
    assert "'look'" in report  # commands attempted
    assert "Sessions that called Argon: 1 / 2" in report


def test_format_session_markdown_renders_turns():
    session = {
        "id": "abc-123",
        "started_at": "2026-04-26T12:00:00+00:00",
        "status": "completed",
        "ending_type": "transmit",
        "player_kind": "agent:claude-sonnet-4-5",
        "final_score": 14,
        "final_o2": 80,
        "final_morale": 72,
        "metadata": {
            "estimated_cost_usd": "0.42",
            "bailout_reason": "ending",
        },
        "turns": [
            {"turn_number": 1, "command": "look",
             "response": "You see a locker.", "current_room": "Sleeping Bay"},
            {"turn_number": 2, "command": "open locker",
             "response": "Empty.", "current_room": "Sleeping Bay"},
        ],
    }
    md = pool.format_session_markdown(session)
    assert "# Playthrough abc-123" in md
    assert "agent:claude-sonnet-4-5" in md
    assert "## Turn 1: `look`" in md
    assert "You see a locker." in md
    assert "## Turn 2: `open locker`" in md
    assert "_room: Sleeping Bay_" in md
    assert "$0.42" in md


def test_format_session_markdown_renders_stuck_moments():
    session = {
        "id": "stuck-1",
        "started_at": "2026-04-26T12:00:00+00:00",
        "status": "stuck",
        "ending_type": None,
        "player_kind": "agent:claude-sonnet-4-5",
        "metadata": {
            "stuck_moments": json.dumps([
                {"turn_start": 5, "turn_end": 14,
                 "room": "Crew Quarters", "window": 10}
            ]),
        },
        "turns": [],
    }
    md = pool.format_session_markdown(session)
    assert "Stuck moments" in md
    assert "turns 5-14 in Crew Quarters" in md


def test_dump_sessions_writes_one_file_per_session(tmp_path):
    db = tmp_path / "dump.sqlite"
    out = tmp_path / "runs"
    from lib.playthrough_db import write_session  # noqa: PLC0415

    for sid in ("a", "b"):
        write_session({
            "session_id": sid,
            "started_at": "2026-04-26T12:00:00+00:00",
            "status": "completed",
            "ending_type": "transmit",
            "player_kind": "agent:claude-sonnet-4-5",
            "turns": [{"turn_number": 1, "command": "look",
                       "response": "...", "current_room": "Sleeping Bay"}],
            "metadata": {"estimated_cost_usd": "0.10"},
        }, db_path=db)

    written = pool.dump_sessions(out_dir=out, db_path=db)
    assert len(written) == 2
    for path in written:
        text = path.read_text()
        assert "# Playthrough" in text
        assert "## Turn 1: `look`" in text


def test_dump_sessions_by_id(tmp_path):
    db = tmp_path / "dump-id.sqlite"
    out = tmp_path / "runs"
    from lib.playthrough_db import write_session  # noqa: PLC0415

    write_session({
        "session_id": "only",
        "started_at": "2026-04-26T12:00:00+00:00",
        "status": "completed",
        "ending_type": "transmit",
        "player_kind": "agent:claude-sonnet-4-5",
        "turns": [],
        "metadata": {},
    }, db_path=db)

    written = pool.dump_sessions(out_dir=out, session_id="only", db_path=db)
    assert len(written) == 1
    assert "only" in written[0].name


def test_dump_sessions_returns_empty_when_no_match(tmp_path):
    db = tmp_path / "empty-dump.sqlite"
    from lib.playthrough_db import init_db  # noqa: PLC0415
    init_db(db)
    written = pool.dump_sessions(out_dir=tmp_path / "runs", db_path=db)
    assert written == []


def test_render_report_filters_by_player_kind(tmp_path):
    db = tmp_path / "filter.sqlite"
    from lib.playthrough_db import write_session  # noqa: PLC0415

    a = {
        "session_id": "a",
        "started_at": "2026-04-26T12:00:00+00:00",
        "status": "completed",
        "ending_type": "transmit",
        "player_kind": "agent:claude-sonnet-4-5",
        "turns": [], "metadata": {"estimated_cost_usd": "0.10"},
    }
    b = {
        "session_id": "b",
        "started_at": "2026-04-26T12:00:00+00:00",
        "status": "completed",
        "ending_type": "transmit",
        "player_kind": "human",
        "turns": [], "metadata": {},
    }
    write_session(a, db_path=db)
    write_session(b, db_path=db)

    report = pool.render_report(
        player_kind="agent:claude-sonnet-4-5", db_path=db
    )
    assert "Runs: 1" in report
    assert "Filter: player_kind = agent:claude-sonnet-4-5" in report
