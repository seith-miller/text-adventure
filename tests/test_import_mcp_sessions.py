"""Tests for `scripts/import_mcp_sessions.py`.

The bridge reads playtest.py-shaped session JSONs from disk and writes
them through `normalize_session_payload` + `write_session`. The tests
focus on end-to-end correctness — does an imported file actually land
in the DB with the right columns populated — and on the argv / error
handling rules a long-running CI batch depends on.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "import_mcp_sessions.py"


def _run(args: list[str], env_db: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["MIRSEND_DB_PATH"] = str(env_db)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def _make_playtest_json(path: Path, session_id: str, turns: int = 3) -> None:
    payload = {
        "session_id": session_id,
        "started_at": "2026-06-08T00:00:00Z",
        "ended_at": "2026-06-08T00:05:00Z",
        "status": "completed",
        "ending_type": "transmit",
        "final_score": 7,
        "final_o2": 50,
        "final_morale": 70,
        "player_kind": "agent:claude-opus-4-7",
        "game_version": "v0.3.0",
        "command_history": [f"cmd-{i}" for i in range(turns)],
        "transcript": "irrelevant for write_session",
    }
    path.write_text(json.dumps(payload))


def test_single_file_lands_in_db(tmp_path):
    db = tmp_path / "playthroughs.sqlite"
    src = tmp_path / "session-A.json"
    _make_playtest_json(src, "sess-A", turns=4)

    result = _run([str(src)], env_db=db)
    assert result.returncode == 0, result.stderr
    assert "imported: session-A.json" in result.stdout

    # Round-trip via get_session to verify the row + per-turn data.
    sys.path.insert(0, str(ROOT))
    from lib.playthrough_db import get_session

    sess = get_session("sess-A", db_path=db)
    assert sess is not None
    assert sess["status"] == "completed"
    assert sess["ending_type"] == "transmit"
    assert sess["final_score"] == 7
    assert sess["final_o2"] == 50
    assert sess["final_morale"] == 70
    assert sess["player_kind"] == "agent:claude-opus-4-7"
    assert sess["game_version"] == "v0.3.0"
    assert len(sess["turns"]) == 4
    assert sess["turns"][0]["command"] == "cmd-0"


def test_glob_arg_expanded_when_shell_does_not(tmp_path):
    """Quoted glob — the shell hands the literal pattern through; the
    script must expand it via Python's glob, not silently skip."""
    db = tmp_path / "playthroughs.sqlite"
    _make_playtest_json(tmp_path / "a.json", "sess-a")
    _make_playtest_json(tmp_path / "b.json", "sess-b")

    pattern = str(tmp_path / "*.json")
    result = _run([pattern], env_db=db)
    assert result.returncode == 0, result.stderr
    assert "imported: a.json" in result.stdout
    assert "imported: b.json" in result.stdout


def test_one_bad_file_does_not_kill_the_batch(tmp_path):
    db = tmp_path / "playthroughs.sqlite"
    good = tmp_path / "good.json"
    bad = tmp_path / "bad.json"
    _make_playtest_json(good, "sess-good")
    bad.write_text("{ not valid json")

    result = _run([str(bad), str(good)], env_db=db)
    # One failure → exit code is the failure count, not 0.
    assert result.returncode == 1
    assert "failed: " in result.stderr
    assert "imported: good.json" in result.stdout


def test_missing_path_reports_failure_not_silent_skip(tmp_path):
    db = tmp_path / "playthroughs.sqlite"
    result = _run([str(tmp_path / "nope.json")], env_db=db)
    assert result.returncode == 1
    assert "failed: " in result.stderr


def test_no_args_returns_nonzero(tmp_path):
    db = tmp_path / "playthroughs.sqlite"
    result = _run([], env_db=db)
    assert result.returncode == 1
    assert "usage" in result.stderr


def test_session_id_falls_back_to_filename_stem_when_missing(tmp_path):
    """If the JSON itself doesn't carry session_id, use path.stem so
    the import still works rather than raising. Subsequent re-imports
    of the same file remain idempotent because write_session is keyed
    on session_id."""
    db = tmp_path / "playthroughs.sqlite"
    src = tmp_path / "no-sid.json"
    src.write_text(json.dumps({
        "started_at": "2026-06-08T00:00:00Z",
        "status": "completed",
        "command_history": ["look"],
    }))

    result = _run([str(src)], env_db=db)
    assert result.returncode == 0, result.stderr

    sys.path.insert(0, str(ROOT))
    from lib.playthrough_db import get_session

    sess = get_session("no-sid", db_path=db)
    assert sess is not None
    assert sess["status"] == "completed"
