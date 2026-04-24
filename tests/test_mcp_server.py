"""Tests for the MIR'S END MCP server.

All tests use a mock backend that simulates the Playwright game driver,
so no browser or game binary is needed.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

# Ensure the repo root is on sys.path so we can import the server module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.mirs_end_mcp import (
    Session,
    _sessions,
    get_backend,
    mcp,
    mirs_end_export_transcript,
    mirs_end_get_state,
    mirs_end_list_sessions,
    mirs_end_restart,
    mirs_end_send_command,
    mirs_end_start_game,
    set_backend,
)


# ---------------------------------------------------------------------------
# Mock backend
# ---------------------------------------------------------------------------

OPENING_TEXT = (
    "You wake to the sound of alarms. Red emergency lighting "
    "floods the Command Module. Through the viewport, Earth hangs "
    "in darkness below."
)

DEFAULT_STATE = {
    "currentRoom": "Command Module",
    "o2": 95,
    "morale": 80,
    "inventory": [],
    "score": 0,
    "turn": 0,
}


class MockBackend:
    """Simulates the Playwright backend without a real browser."""

    _counter = 0

    def __init__(self):
        self._command_count = 0

    async def ensure_browser(self):
        pass

    async def new_session(self) -> Session:
        MockBackend._counter += 1
        session = Session(
            session_id=f"mock-{MockBackend._counter:05d}",
            started_at=time.time(),
        )
        session.transcript.append(OPENING_TEXT)
        session._last_state = dict(DEFAULT_STATE)
        return session

    async def send_command(self, session: Session, command: str) -> str:
        self._command_count += 1
        response = f"You typed: {command}. The station hums quietly."
        session.turn_count += 1
        session.command_history.append(command)
        session.transcript.append(f"> {command}")
        session.transcript.append(response)
        state = dict(DEFAULT_STATE)
        state["turn"] = session.turn_count
        if command == "take flashlight":
            state["inventory"] = ["flashlight"]
        session._last_state = state
        return response

    async def read_state(self, session: Session) -> dict:
        return session._last_state

    async def restart(self, session: Session) -> str:
        session.turn_count = 0
        session.command_history.clear()
        session.transcript.clear()
        session.transcript.append(OPENING_TEXT)
        session._last_state = dict(DEFAULT_STATE)
        return OPENING_TEXT

    async def close_session(self, session: Session) -> None:
        pass

    async def shutdown(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_sessions():
    """Clear session store and inject mock backend before each test."""
    _sessions.clear()
    set_backend(MockBackend())
    yield
    _sessions.clear()


# ---------------------------------------------------------------------------
# Tool: mirs_end_start_game
# ---------------------------------------------------------------------------

class TestStartGame:
    def test_returns_session_id(self):
        result = asyncio.run(mirs_end_start_game())
        assert "session_id" in result
        assert isinstance(result["session_id"], str)
        assert len(result["session_id"]) > 0

    def test_returns_opening_text(self):
        result = asyncio.run(mirs_end_start_game())
        assert "opening_text" in result
        assert "wake" in result["opening_text"].lower()

    def test_returns_initial_state(self):
        result = asyncio.run(mirs_end_start_game())
        assert "state" in result
        state = result["state"]
        assert state["currentRoom"] == "Command Module"
        assert state["o2"] == 95
        assert state["morale"] == 80

    def test_session_persisted_in_store(self):
        result = asyncio.run(mirs_end_start_game())
        assert result["session_id"] in _sessions

    def test_multiple_sessions(self):
        r1 = asyncio.run(mirs_end_start_game())
        r2 = asyncio.run(mirs_end_start_game())
        assert r1["session_id"] != r2["session_id"]
        assert len(_sessions) == 2


# ---------------------------------------------------------------------------
# Tool: mirs_end_send_command
# ---------------------------------------------------------------------------

class TestSendCommand:
    def _start(self) -> str:
        return asyncio.run(mirs_end_start_game())["session_id"]

    def test_returns_response_text(self):
        sid = self._start()
        result = asyncio.run(mirs_end_send_command(sid, "look"))
        assert "response_text" in result
        assert "look" in result["response_text"].lower()

    def test_returns_updated_state(self):
        sid = self._start()
        result = asyncio.run(mirs_end_send_command(sid, "look"))
        assert "state" in result
        assert result["state"]["turn"] == 1

    def test_increments_turn_count(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        asyncio.run(mirs_end_send_command(sid, "inventory"))
        session = _sessions[sid]
        assert session.turn_count == 2

    def test_records_command_history(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        asyncio.run(mirs_end_send_command(sid, "go north"))
        session = _sessions[sid]
        assert session.command_history == ["look", "go north"]

    def test_appends_transcript(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        session = _sessions[sid]
        # Opening text + "> look" + response
        assert len(session.transcript) == 3
        assert session.transcript[1] == "> look"

    def test_unknown_session_raises(self):
        with pytest.raises(ValueError, match="Unknown session"):
            asyncio.run(mirs_end_send_command("nonexistent", "look"))

    def test_inventory_pickup(self):
        sid = self._start()
        result = asyncio.run(mirs_end_send_command(sid, "take flashlight"))
        assert result["state"]["inventory"] == ["flashlight"]


# ---------------------------------------------------------------------------
# Tool: mirs_end_get_state
# ---------------------------------------------------------------------------

class TestGetState:
    def _start(self) -> str:
        return asyncio.run(mirs_end_start_game())["session_id"]

    def test_returns_all_fields(self):
        sid = self._start()
        result = asyncio.run(mirs_end_get_state(sid))
        expected_keys = {"currentRoom", "o2", "morale", "inventory", "score", "turn"}
        assert expected_keys == set(result.keys())

    def test_initial_state_values(self):
        sid = self._start()
        result = asyncio.run(mirs_end_get_state(sid))
        assert result["currentRoom"] == "Command Module"
        assert result["o2"] == 95
        assert result["morale"] == 80
        assert result["inventory"] == []
        assert result["score"] == 0
        assert result["turn"] == 0

    def test_state_after_commands(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        result = asyncio.run(mirs_end_get_state(sid))
        assert result["turn"] == 1

    def test_unknown_session_raises(self):
        with pytest.raises(ValueError, match="Unknown session"):
            asyncio.run(mirs_end_get_state("nonexistent"))


# ---------------------------------------------------------------------------
# Tool: mirs_end_export_transcript
# ---------------------------------------------------------------------------

class TestExportTranscript:
    def _start(self) -> str:
        return asyncio.run(mirs_end_start_game())["session_id"]

    def test_returns_transcript(self):
        sid = self._start()
        result = asyncio.run(mirs_end_export_transcript(sid))
        assert "transcript" in result
        assert isinstance(result["transcript"], list)
        assert len(result["transcript"]) >= 1

    def test_returns_command_history(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        result = asyncio.run(mirs_end_export_transcript(sid))
        assert result["commandHistory"] == ["look"]

    def test_returns_final_state(self):
        sid = self._start()
        result = asyncio.run(mirs_end_export_transcript(sid))
        assert "finalState" in result
        assert result["finalState"]["currentRoom"] == "Command Module"

    def test_transcript_grows_with_commands(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        asyncio.run(mirs_end_send_command(sid, "go north"))
        result = asyncio.run(mirs_end_export_transcript(sid))
        # opening + ("> look" + response) + ("> go north" + response)
        assert len(result["transcript"]) == 5
        assert len(result["commandHistory"]) == 2

    def test_unknown_session_raises(self):
        with pytest.raises(ValueError, match="Unknown session"):
            asyncio.run(mirs_end_export_transcript("nonexistent"))


# ---------------------------------------------------------------------------
# Tool: mirs_end_restart
# ---------------------------------------------------------------------------

class TestRestart:
    def _start(self) -> str:
        return asyncio.run(mirs_end_start_game())["session_id"]

    def test_returns_opening_text(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        result = asyncio.run(mirs_end_restart(sid))
        assert "opening_text" in result
        assert "wake" in result["opening_text"].lower()

    def test_resets_state(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        result = asyncio.run(mirs_end_restart(sid))
        assert result["state"]["turn"] == 0

    def test_clears_transcript(self):
        sid = self._start()
        asyncio.run(mirs_end_send_command(sid, "look"))
        asyncio.run(mirs_end_restart(sid))
        session = _sessions[sid]
        assert len(session.transcript) == 1  # just the opening
        assert session.command_history == []
        assert session.turn_count == 0

    def test_session_id_preserved(self):
        sid = self._start()
        asyncio.run(mirs_end_restart(sid))
        assert sid in _sessions

    def test_unknown_session_raises(self):
        with pytest.raises(ValueError, match="Unknown session"):
            asyncio.run(mirs_end_restart("nonexistent"))


# ---------------------------------------------------------------------------
# Tool: mirs_end_list_sessions
# ---------------------------------------------------------------------------

class TestListSessions:
    def test_empty_initially(self):
        result = asyncio.run(mirs_end_list_sessions())
        assert result == []

    def test_lists_one_session(self):
        asyncio.run(mirs_end_start_game())
        result = asyncio.run(mirs_end_list_sessions())
        assert len(result) == 1
        entry = result[0]
        assert "session_id" in entry
        assert "started_at" in entry
        assert "turn_count" in entry
        assert entry["turn_count"] == 0

    def test_lists_multiple_sessions(self):
        asyncio.run(mirs_end_start_game())
        asyncio.run(mirs_end_start_game())
        asyncio.run(mirs_end_start_game())
        result = asyncio.run(mirs_end_list_sessions())
        assert len(result) == 3
        ids = {s["session_id"] for s in result}
        assert len(ids) == 3

    def test_turn_count_updates(self):
        r = asyncio.run(mirs_end_start_game())
        sid = r["session_id"]
        asyncio.run(mirs_end_send_command(sid, "look"))
        asyncio.run(mirs_end_send_command(sid, "go north"))
        result = asyncio.run(mirs_end_list_sessions())
        entry = [s for s in result if s["session_id"] == sid][0]
        assert entry["turn_count"] == 2


# ---------------------------------------------------------------------------
# Session persistence across tool calls
# ---------------------------------------------------------------------------

class TestSessionPersistence:
    """Verify that state persists across multiple tool invocations."""

    def test_state_persists_across_calls(self):
        r = asyncio.run(mirs_end_start_game())
        sid = r["session_id"]

        asyncio.run(mirs_end_send_command(sid, "look"))
        asyncio.run(mirs_end_send_command(sid, "take flashlight"))

        state = asyncio.run(mirs_end_get_state(sid))
        assert state["turn"] == 2
        assert state["inventory"] == ["flashlight"]

        export = asyncio.run(mirs_end_export_transcript(sid))
        assert len(export["commandHistory"]) == 2
        assert export["commandHistory"] == ["look", "take flashlight"]

    def test_restart_then_play(self):
        r = asyncio.run(mirs_end_start_game())
        sid = r["session_id"]

        asyncio.run(mirs_end_send_command(sid, "look"))
        asyncio.run(mirs_end_restart(sid))
        asyncio.run(mirs_end_send_command(sid, "inventory"))

        state = asyncio.run(mirs_end_get_state(sid))
        assert state["turn"] == 1

        export = asyncio.run(mirs_end_export_transcript(sid))
        assert export["commandHistory"] == ["inventory"]


# ---------------------------------------------------------------------------
# MCP server registration
# ---------------------------------------------------------------------------

class TestMCPRegistration:
    """Verify the MCP server has the expected tools registered."""

    def test_server_name(self):
        assert mcp.name == "MIR'S END"

    def test_all_tools_registered(self):
        tools = mcp._tool_manager._tools
        expected = {
            "mirs_end_start_game",
            "mirs_end_send_command",
            "mirs_end_get_state",
            "mirs_end_export_transcript",
            "mirs_end_restart",
            "mirs_end_list_sessions",
        }
        assert expected == set(tools.keys())
