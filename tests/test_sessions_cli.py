"""Tests for scripts/sessions.py CLI and lib/playthrough_db queries."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

# Make lib/ importable
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "lib"))
sys.path.insert(0, str(_repo_root / "scripts"))

from playthrough_db import init_db, queries  # noqa: E402

# Import the CLI's main() for integration tests
import sessions as sessions_cli  # noqa: E402

# ── Fixtures ─────────────────────────────────────────────────────────

SAMPLE_SESSIONS = [
    {
        "id": "sess-001",
        "started": "2025-06-01T10:00:00Z",
        "ended": "2025-06-01T11:00:00Z",
        "player_kind": "human",
        "ending": "escape",
        "score": 85.0,
        "source_json": json.dumps({"session": {"id": "sess-001"}, "turns": [], "ai_calls": []}),
    },
    {
        "id": "sess-002",
        "started": "2025-06-02T10:00:00Z",
        "ended": "2025-06-02T12:00:00Z",
        "player_kind": "agent",
        "ending": "death",
        "score": 20.0,
        "source_json": None,
    },
    {
        "id": "sess-003",
        "started": "2025-07-01T08:00:00Z",
        "ended": None,
        "player_kind": "test",
        "ending": None,
        "score": None,
        "source_json": None,
    },
]

SAMPLE_TURNS = [
    ("sess-001", 1, "look", "You see the reactor room.", '{"reactor": "nominal"}'),
    ("sess-001", 2, "go north", "You enter the corridor.", '{"location": "corridor"}'),
    ("sess-001", 3, "examine panel", "A blinking status panel.", '{"panel": true}'),
    ("sess-002", 1, "look", "Darkness.", '{"dark": true}'),
    ("sess-002", 2, "scream", "Nobody hears you.", None),
]

SAMPLE_AI_CALLS = [
    ("sess-001", 1, "station-ai", "gpt-4", 0.03, "Reactor status nominal."),
    ("sess-001", 1, "director", "gpt-4", 0.02, "Build tension."),
    ("sess-001", 2, "narrator", "gpt-3.5", 0.005, "The corridor stretches ahead."),
    ("sess-002", 1, "station-ai", "gpt-4", 0.03, "Systems offline."),
    ("sess-002", 1, "director", "gpt-4", 0.02, "Introduce threat."),
]


@pytest.fixture
def db(tmp_path):
    """Create a populated in-memory-like temp database."""
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)

    for s in SAMPLE_SESSIONS:
        conn.execute(
            "INSERT INTO sessions (id, started, ended, player_kind, ending, score, source_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (s["id"], s["started"], s["ended"], s["player_kind"], s["ending"], s["score"], s["source_json"]),
        )

    for t in SAMPLE_TURNS:
        conn.execute(
            "INSERT INTO turns (session_id, turn_number, command, response, state) VALUES (?, ?, ?, ?, ?)",
            t,
        )

    for a in SAMPLE_AI_CALLS:
        conn.execute(
            "INSERT INTO ai_calls (session_id, turn_number, role, model, cost, response) VALUES (?, ?, ?, ?, ?, ?)",
            a,
        )

    conn.commit()
    return conn, str(db_path)


@pytest.fixture
def empty_db(tmp_path):
    """Create an empty database."""
    db_path = tmp_path / "empty.db"
    conn = init_db(db_path)
    return conn, str(db_path)


# ── Query-level tests ────────────────────────────────────────────────


class TestListSessions:
    def test_returns_all(self, db):
        conn, _ = db
        rows = queries.list_sessions(conn, limit=100)
        assert len(rows) == 3

    def test_limit(self, db):
        conn, _ = db
        rows = queries.list_sessions(conn, limit=1)
        assert len(rows) == 1

    def test_filter_player_kind(self, db):
        conn, _ = db
        rows = queries.list_sessions(conn, player_kind="human")
        assert len(rows) == 1
        assert rows[0]["id"] == "sess-001"

    def test_filter_ending(self, db):
        conn, _ = db
        rows = queries.list_sessions(conn, ending="death")
        assert len(rows) == 1
        assert rows[0]["id"] == "sess-002"

    def test_filter_since(self, db):
        conn, _ = db
        rows = queries.list_sessions(conn, since="2025-06-15")
        assert len(rows) == 1
        assert rows[0]["id"] == "sess-003"

    def test_combined_filters(self, db):
        conn, _ = db
        rows = queries.list_sessions(conn, player_kind="human", since="2025-01-01")
        assert len(rows) == 1

    def test_includes_turn_count(self, db):
        conn, _ = db
        rows = queries.list_sessions(conn, player_kind="human")
        assert rows[0]["turn_count"] == 3

    def test_empty_db(self, empty_db):
        conn, _ = empty_db
        rows = queries.list_sessions(conn)
        assert rows == []


class TestGetSession:
    def test_found(self, db):
        conn, _ = db
        s = queries.get_session(conn, "sess-001")
        assert s is not None
        assert s["id"] == "sess-001"
        assert s["turn_count"] == 3
        assert s["ai_call_count"] == 3
        assert s["total_cost"] == pytest.approx(0.055)

    def test_not_found(self, db):
        conn, _ = db
        assert queries.get_session(conn, "nonexistent") is None

    def test_empty_db(self, empty_db):
        conn, _ = empty_db
        assert queries.get_session(conn, "anything") is None


class TestGetTurns:
    def test_all_turns(self, db):
        conn, _ = db
        turns = queries.get_turns(conn, "sess-001")
        assert len(turns) == 3

    def test_single_turn(self, db):
        conn, _ = db
        turns = queries.get_turns(conn, "sess-001", turn=2)
        assert len(turns) == 1
        assert turns[0]["command"] == "go north"

    def test_range(self, db):
        conn, _ = db
        turns = queries.get_turns(conn, "sess-001", range_start=1, range_end=2)
        assert len(turns) == 2

    def test_no_turns_for_session(self, db):
        conn, _ = db
        turns = queries.get_turns(conn, "sess-003")
        assert turns == []


class TestGetAiCalls:
    def test_all_calls(self, db):
        conn, _ = db
        calls = queries.get_ai_calls(conn, "sess-001")
        assert len(calls) == 3

    def test_filter_by_role(self, db):
        conn, _ = db
        calls = queries.get_ai_calls(conn, "sess-001", role="station-ai")
        assert len(calls) == 1
        assert calls[0]["role"] == "station-ai"

    def test_no_calls(self, db):
        conn, _ = db
        calls = queries.get_ai_calls(conn, "sess-003")
        assert calls == []


class TestCostReport:
    def test_by_player(self, db):
        conn, _ = db
        rows = queries.cost_report(conn, by="player")
        assert len(rows) >= 1
        # human sessions have highest cost
        player_kinds = {r["group_key"] for r in rows}
        assert "human" in player_kinds

    def test_by_role(self, db):
        conn, _ = db
        rows = queries.cost_report(conn, by="role")
        roles = {r["group_key"] for r in rows}
        assert "station-ai" in roles
        assert "director" in roles

    def test_by_day(self, db):
        conn, _ = db
        rows = queries.cost_report(conn, by="day")
        assert len(rows) >= 1

    def test_since_filter(self, db):
        conn, _ = db
        rows = queries.cost_report(conn, by="player", since="2025-06-02")
        # Only sess-002 costs should be included
        assert len(rows) == 1
        assert rows[0]["group_key"] == "agent"

    def test_invalid_by(self, db):
        conn, _ = db
        with pytest.raises(ValueError):
            queries.cost_report(conn, by="invalid")

    def test_empty_db(self, empty_db):
        conn, _ = empty_db
        rows = queries.cost_report(conn, by="player")
        assert rows == []


class TestCompareSessions:
    def test_compare(self, db):
        conn, _ = db
        result = queries.compare_sessions(conn, "sess-001", "sess-002")
        assert result is not None
        assert result["session_1"]["turn_count"] == 3
        assert result["session_2"]["turn_count"] == 2
        assert result["diffs"]["turn_count"] == 1

    def test_missing_session(self, db):
        conn, _ = db
        assert queries.compare_sessions(conn, "sess-001", "nonexistent") is None

    def test_ai_distribution(self, db):
        conn, _ = db
        result = queries.compare_sessions(conn, "sess-001", "sess-002")
        dist1 = result["ai_distribution"]["sess-001"]
        assert dist1["station-ai"] == 1
        assert dist1["director"] == 1
        assert dist1["narrator"] == 1


class TestExportSession:
    def test_with_source_json(self, db):
        conn, _ = db
        data = queries.export_session(conn, "sess-001")
        assert data is not None
        assert data["session"]["id"] == "sess-001"

    def test_without_source_json(self, db):
        conn, _ = db
        data = queries.export_session(conn, "sess-002")
        assert data is not None
        assert "session" in data
        assert "turns" in data
        assert "ai_calls" in data

    def test_not_found(self, db):
        conn, _ = db
        assert queries.export_session(conn, "nonexistent") is None


class TestDeleteSession:
    def test_delete(self, db):
        conn, _ = db
        assert queries.delete_session(conn, "sess-001") is True
        assert queries.get_session(conn, "sess-001") is None
        # Child rows should be gone too (FK cascade)
        assert queries.get_turns(conn, "sess-001") == []
        assert queries.get_ai_calls(conn, "sess-001") == []

    def test_delete_nonexistent(self, db):
        conn, _ = db
        assert queries.delete_session(conn, "nonexistent") is False


# ── CLI integration tests ────────────────────────────────────────────


class TestCLIList:
    def test_list_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "list", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 3

    def test_list_table(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "list"])
        out = capsys.readouterr().out
        assert "sess-001" in out

    def test_list_with_filters_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "list", "--player-kind", "agent", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 1
        assert out[0]["id"] == "sess-002"

    def test_list_empty_db_json(self, empty_db, capsys):
        _, db_path = empty_db
        sessions_cli.main(["--db", db_path, "list", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert out == []

    def test_list_empty_db_table(self, empty_db, capsys):
        _, db_path = empty_db
        sessions_cli.main(["--db", db_path, "list"])
        out = capsys.readouterr().out
        assert "no results" in out


class TestCLIShow:
    def test_show_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "show", "sess-001", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert out["id"] == "sess-001"
        assert out["turn_count"] == 3

    def test_show_table(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "show", "sess-001"])
        out = capsys.readouterr().out
        assert "sess-001" in out
        assert "turn_count" in out

    def test_show_not_found(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path, "show", "nonexistent"])
        assert exc_info.value.code == 1


class TestCLITurns:
    def test_turns_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "turns", "sess-001", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 3

    def test_turns_single(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "turns", "sess-001", "--turn", "2", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 1
        assert out[0]["command"] == "go north"

    def test_turns_range(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "turns", "sess-001", "--range", "1-2", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2

    def test_turns_not_found(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path, "turns", "nonexistent"])
        assert exc_info.value.code == 1


class TestCLIAiCalls:
    def test_ai_calls_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "ai-calls", "sess-001", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 3

    def test_ai_calls_filter_role(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "ai-calls", "sess-001", "--role", "narrator", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 1
        assert out[0]["role"] == "narrator"

    def test_ai_calls_not_found(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path, "ai-calls", "nonexistent"])
        assert exc_info.value.code == 1


class TestCLICosts:
    def test_costs_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "costs", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert len(out) >= 1

    def test_costs_by_role_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "costs", "--by", "role", "--json"])
        out = json.loads(capsys.readouterr().out)
        roles = {r["group_key"] for r in out}
        assert "station-ai" in roles

    def test_costs_empty_db(self, empty_db, capsys):
        _, db_path = empty_db
        sessions_cli.main(["--db", db_path, "costs", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert out == []


class TestCLICompare:
    def test_compare_json(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "compare", "sess-001", "sess-002", "--json"])
        out = json.loads(capsys.readouterr().out)
        assert "diffs" in out
        assert out["diffs"]["turn_count"] == 1

    def test_compare_table(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "compare", "sess-001", "sess-002"])
        out = capsys.readouterr().out
        assert "Turn count" in out

    def test_compare_not_found(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path, "compare", "sess-001", "nonexistent"])
        assert exc_info.value.code == 1


class TestCLIExport:
    def test_export(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "export", "sess-001"])
        out = json.loads(capsys.readouterr().out)
        assert out["session"]["id"] == "sess-001"

    def test_export_not_found(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path, "export", "nonexistent"])
        assert exc_info.value.code == 1


class TestCLIDelete:
    def test_delete_without_confirm(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path, "delete", "sess-001"])
        assert exc_info.value.code == 1

    def test_delete_with_confirm(self, db, capsys):
        _, db_path = db
        sessions_cli.main(["--db", db_path, "delete", "sess-001", "--confirm"])
        out = capsys.readouterr().out
        assert "Deleted" in out

    def test_delete_nonexistent(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path, "delete", "nonexistent", "--confirm"])
        assert exc_info.value.code == 1


class TestCLINoCommand:
    def test_no_command_exits(self, db):
        _, db_path = db
        with pytest.raises(SystemExit) as exc_info:
            sessions_cli.main(["--db", db_path])
        assert exc_info.value.code == 1
