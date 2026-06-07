#!/usr/bin/env python3
"""MCP server for MIR'S END: per-turn interactive play.

Exposes MIR'S END as a tool-integrated game for an external LLM player.
Uses Playwright (headless Chromium) to drive the existing web harness,
giving identical behavior to the real browser game.

Transport: stdio (matches Claude Code .mcp.json expectations).

Usage:
    python scripts/mirs_end_mcp.py
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Session data
# ---------------------------------------------------------------------------

@dataclass
class Session:
    """One active game session backed by a Playwright browser context."""

    session_id: str
    started_at: float
    turn_count: int = 0
    transcript: list[str] = field(default_factory=list)
    command_history: list[str] = field(default_factory=list)
    page: Any = None          # playwright Page (set after launch)
    context: Any = None       # browser context
    _last_state: dict = field(default_factory=dict)
    _scrollback_len: int = 0  # chars of #story-output already consumed


# ---------------------------------------------------------------------------
# Backend abstraction
# ---------------------------------------------------------------------------

class PlaywrightBackend:
    """Drives the game through headless Chromium + the existing web harness."""

    def __init__(self, game_url: str | None = None):
        repo_root = Path(__file__).resolve().parent.parent
        self._repo_root = repo_root
        self._explicit_url = game_url
        self._game_url = game_url  # set in ensure_browser if not explicit
        self._browser: Any = None
        self._playwright: Any = None
        self._http_server: Any = None
        self._http_thread: Any = None

    def _start_local_http(self) -> str:
        """
        Serve game/ over HTTP on a free local port.

        Chromium blocks `fetch` on file:// origins, which the game uses
        to load story.ulx and assets. Spinning up a tiny in-process HTTP
        server gives the page an http:// origin without requiring the
        caller to manage a separate web server.
        """
        import http.server
        import socketserver
        import threading

        game_dir = str(self._repo_root / "game")

        class _Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=game_dir, **kwargs)

            def log_message(self, *args, **kwargs):
                pass  # silence per-request logging

        class _Server(socketserver.ThreadingTCPServer):
            allow_reuse_address = True
            daemon_threads = True

        self._http_server = _Server(("127.0.0.1", 0), _Handler)
        port = self._http_server.server_address[1]
        self._http_thread = threading.Thread(
            target=self._http_server.serve_forever, daemon=True
        )
        self._http_thread.start()
        return f"http://127.0.0.1:{port}/play.html"

    async def ensure_browser(self) -> None:
        if self._browser is not None:
            return
        from playwright.async_api import async_playwright
        if self._game_url is None:
            self._game_url = self._start_local_http()
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)

    async def new_session(self) -> Session:
        await self.ensure_browser()
        session = Session(
            session_id=uuid.uuid4().hex[:12],
            started_at=time.time(),
        )
        session.context = await self._browser.new_context()
        session.page = await session.context.new_page()
        await session.page.goto(self._game_url)

        # Wait for title screen, click New Game
        await session.page.locator("#title-screen").wait_for(state="visible")
        await session.page.click("#menu-new-game")

        # Skip intro
        await session.page.wait_for_timeout(300)
        await session.page.keyboard.press("Escape")

        # Wait for first narrative
        await session.page.locator("#story-output").filter(
            has_text="Crew Quarters"
        ).wait_for(timeout=15_000)

        opening = await self._get_story_text(session.page)
        session.transcript.append(opening)
        session._scrollback_len = len(opening)
        session._last_state = await self._read_state(session.page)
        return session

    async def send_command(self, session: Session, command: str) -> str:
        page = session.page
        # Type into GlkOte line input (real interpreter path)
        glk = page.locator("#windowport input.LineInput")
        if await glk.count() > 0:
            await glk.focus()
            await page.keyboard.type(command)
            await page.keyboard.press("Enter")
        else:
            inp = page.locator("#command-input")
            await inp.fill(command)
            await inp.press("Enter")

        # Wait for new output to appear
        await page.wait_for_timeout(500)

        # #story-output is cumulative (the whole scrollback). Slice off
        # the prefix we've already returned so the per-turn response
        # contains only the new content.
        full_text = await self._get_story_text(page)
        new_text = full_text[session._scrollback_len:].strip()
        session._scrollback_len = len(full_text)

        session.turn_count += 1
        session.command_history.append(command)
        session.transcript.append(f"> {command}")
        session.transcript.append(new_text)
        session._last_state = await self._read_state(page)
        return new_text

    async def read_state(self, session: Session) -> dict:
        session._last_state = await self._read_state(session.page)
        return session._last_state

    async def restart(self, session: Session) -> str:
        page = session.page
        await page.goto(self._game_url)
        await page.locator("#title-screen").wait_for(state="visible")
        await page.click("#menu-new-game")
        await page.wait_for_timeout(300)
        await page.keyboard.press("Escape")
        await page.locator("#story-output").filter(
            has_text="Crew Quarters"
        ).wait_for(timeout=15_000)

        opening = await self._get_story_text(page)
        session.turn_count = 0
        session.command_history.clear()
        session.transcript.clear()
        session.transcript.append(opening)
        session._scrollback_len = len(opening)
        session._last_state = await self._read_state(page)
        return opening

    async def close_session(self, session: Session) -> None:
        if session.context:
            await session.context.close()
            session.context = None
            session.page = None

    async def shutdown(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()
            self._http_server = None

    # -- internal helpers --------------------------------------------------

    async def _get_story_text(self, page: Any) -> str:
        return await page.locator("#story-output").text_content() or ""

    async def _read_state(self, page: Any) -> dict:
        state = await page.evaluate("""() => {
            const m = window.MirsEnd;
            if (!m) return {};
            const s = m.getState();
            return {
                currentRoom: s.currentRoom || 'unknown',
                o2: s.o2 ?? 100,
                morale: s.morale ?? 100,
                inventory: s.inventory || [],
                score: 0,
                turn: (s.commandHistory || []).length
            };
        }""")
        return state or {}


# ---------------------------------------------------------------------------
# Session store
# ---------------------------------------------------------------------------

_sessions: dict[str, Session] = {}
_backend: PlaywrightBackend | None = None


def get_backend() -> PlaywrightBackend:
    global _backend
    if _backend is None:
        _backend = PlaywrightBackend()
    return _backend


def set_backend(backend: Any) -> None:
    """Inject a custom backend (used in tests)."""
    global _backend
    _backend = backend


def _get_session(session_id: str) -> Session:
    if session_id not in _sessions:
        raise ValueError(f"Unknown session: {session_id}")
    return _sessions[session_id]


# ---------------------------------------------------------------------------
# MCP server definition
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "MIR'S END",
    instructions=(
        "MIR'S END is an interactive survival text adventure set aboard "
        "the Mir-3 space station. Use the tools to play the game turn by turn."
    ),
)


@mcp.tool()
async def mirs_end_start_game() -> dict:
    """Start a new game of MIR'S END.

    Returns the session ID, opening narrative text, and initial game state.
    Use the session_id in subsequent calls to interact with this game session.
    """
    backend = get_backend()
    session = await backend.new_session()
    _sessions[session.session_id] = session
    return {
        "session_id": session.session_id,
        "opening_text": session.transcript[0] if session.transcript else "",
        "state": session._last_state,
    }


@mcp.tool()
async def mirs_end_send_command(session_id: str, command: str) -> dict:
    """Send a command to the game and get the response.

    This is the primary tool for playing the game. Send text commands like
    'look', 'go north', 'take lamp', etc. Each call is one game turn.

    Args:
        session_id: The session ID from mirs_end_start_game.
        command: The text command to send to the game.
    """
    session = _get_session(session_id)
    backend = get_backend()
    response_text = await backend.send_command(session, command)
    return {
        "response_text": response_text,
        "state": session._last_state,
    }


@mcp.tool()
async def mirs_end_get_state(session_id: str) -> dict:
    """Get the current game state without taking an action.

    Args:
        session_id: The session ID from mirs_end_start_game.

    Returns current room, O2, morale, inventory, score, and turn count.
    """
    session = _get_session(session_id)
    backend = get_backend()
    state = await backend.read_state(session)
    return {
        "currentRoom": state.get("currentRoom", "unknown"),
        "o2": state.get("o2", 100),
        "morale": state.get("morale", 100),
        "inventory": state.get("inventory", []),
        "score": state.get("score", 0),
        "turn": state.get("turn", 0),
    }


@mcp.tool()
async def mirs_end_export_transcript(session_id: str) -> dict:
    """Export the full transcript and command history for a session.

    Args:
        session_id: The session ID from mirs_end_start_game.

    Returns the complete transcript, command history, and final game state.
    """
    session = _get_session(session_id)
    backend = get_backend()
    state = await backend.read_state(session)
    return {
        "transcript": session.transcript,
        "commandHistory": session.command_history,
        "finalState": state,
    }


@mcp.tool()
async def mirs_end_restart(session_id: str) -> dict:
    """Restart the game within an existing session.

    Resets the game to the beginning while keeping the same session ID.

    Args:
        session_id: The session ID from mirs_end_start_game.
    """
    session = _get_session(session_id)
    backend = get_backend()
    opening = await backend.restart(session)
    return {
        "opening_text": opening,
        "state": session._last_state,
    }


@mcp.tool()
async def mirs_end_list_sessions() -> list[dict]:
    """List all active game sessions.

    Returns session IDs, start times, and turn counts for all active sessions.
    """
    return [
        {
            "session_id": s.session_id,
            "started_at": s.started_at,
            "turn_count": s.turn_count,
        }
        for s in _sessions.values()
    ]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP server on stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
