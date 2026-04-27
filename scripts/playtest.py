#!/usr/bin/env python3
"""
Sandboxed AI playtest driver for MIR'S END.

Runs a Claude session whose tool catalog contains exactly four MCP tools
and nothing else. No file system. No shell. No web fetch. The agent has
no path to read the codebase, the writing samples, or the design docs.
It can only call the four tools below.

System prompt is one sentence: "Play a text-based adventure game using
the available tools."

This is the structural answer to "play like a human": deny the agent
access to developer artifacts at the SDK layer, not via prompt
negotiation. See issue #107 for the design rationale.

## Usage

```
ANTHROPIC_API_KEY=... python3 scripts/playtest.py
```

Optional flags:

  --model MODEL          Claude model id (default: claude-sonnet-4-5)
  --max-turns N          Hard cap on turns (default: 200)
  --stuck-window N       Bail out after N turns of no state change (default: 10)
  --no-ingest            Skip POST to /v1/sessions
  --proxy-url URL        Override proxy URL (default: http://localhost:8787)
  --output PATH          Write transcript to this path on completion

## What the agent CAN see

Only what the game prints in response to its commands. No filesystem.
No additional tools.

## What the agent CANNOT see

The repo source. Writing samples. Persona prompt. Design docs. Earlier
transcripts. Walkthroughs. README.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TURNS = 200
DEFAULT_STUCK_WINDOW = 10
DEFAULT_PROXY_URL = "http://localhost:8787"

SYSTEM_PROMPT = "Play a text-based adventure game using the available tools."

TOOLS_SCHEMA = [
    {
        "name": "mirs_end_start_game",
        "description": (
            "Start a new game. Returns a session_id, the opening narrative, "
            "and the initial state. Call this first."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "mirs_end_send_command",
        "description": (
            "Send a command to the game and get the response. Use plain text "
            "commands like 'look', 'go north', 'take lamp'. One command per call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "command": {"type": "string"},
            },
            "required": ["session_id", "command"],
        },
    },
    {
        "name": "mirs_end_get_state",
        "description": (
            "Get the current game state without taking an action. Returns "
            "current room, O2, morale, inventory, score, and turn count."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"session_id": {"type": "string"}},
            "required": ["session_id"],
        },
    },
    {
        "name": "mirs_end_export_transcript",
        "description": (
            "Export the full transcript and command history for the session. "
            "Use this when the game has reached an ending."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"session_id": {"type": "string"}},
            "required": ["session_id"],
        },
    },
]


def _load_mcp_module():
    """Import scripts/mirs_end_mcp.py as a module so we can use its backend."""
    spec = importlib.util.spec_from_file_location(
        "mirs_end_mcp", str(REPO_ROOT / "scripts" / "mirs_end_mcp.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load mirs_end_mcp module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class GameBridge:
    """
    Direct bridge to the Mir's End MCP server's backend. This is the
    same code the MCP server uses; we call it without going through the
    stdio MCP protocol because that overhead is unnecessary here.

    The agent's tool surface is fully controlled by what we expose in
    TOOLS_SCHEMA above. The agent has no other path to call code.
    """

    def __init__(self) -> None:
        mcp_module = _load_mcp_module()
        self._backend = mcp_module.PlaywrightBackend()
        self._sessions: dict[str, Any] = {}
        self._loop = asyncio.new_event_loop()

    def start_game(self) -> dict:
        async def _run() -> dict:
            session = await self._backend.new_session()
            self._sessions[session.session_id] = session
            return {
                "session_id": session.session_id,
                "opening_text": session.transcript[0] if session.transcript else "",
                "state": session._last_state,
            }

        return self._loop.run_until_complete(_run())

    def send_command(self, session_id: str, command: str) -> dict:
        session = self._sessions.get(session_id)
        if session is None:
            return {"error": f"unknown session_id: {session_id}"}

        async def _run() -> dict:
            response_text = await self._backend.send_command(session, command)
            return {
                "response_text": response_text,
                "state": session._last_state,
                "turn": len(session.command_history),
            }

        return self._loop.run_until_complete(_run())

    def get_state(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if session is None:
            return {"error": f"unknown session_id: {session_id}"}
        return {"state": session._last_state, "turn": len(session.command_history)}

    def export_transcript(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        if session is None:
            return {"error": f"unknown session_id: {session_id}"}
        return {
            "session_id": session.session_id,
            "started_at": session.started_at,
            "command_history": list(session.command_history),
            "transcript": "\n".join(session.transcript),
            "final_state": session._last_state,
        }

    def close(self) -> None:
        async def _run() -> None:
            for session in self._sessions.values():
                await self._backend.close_session(session)

        try:
            self._loop.run_until_complete(_run())
        except Exception:
            pass
        finally:
            self._loop.close()


ENDING_MARKERS = (
    "[Game ended]",
    "*** ",  # Inform 7 standard ending banner prefix
    "You have suffocated",
    "Begin preparations",  # transmit climax
)


def _is_ending(state: dict, response: str) -> bool:
    if not response:
        return False
    return any(marker in response for marker in ENDING_MARKERS)


def _state_signature(state: dict) -> str:
    if not isinstance(state, dict):
        return ""
    parts = [
        state.get("currentRoom", ""),
        state.get("o2", ""),
        state.get("morale", ""),
        ",".join(sorted(state.get("inventory", []))) if isinstance(state.get("inventory"), list) else "",
        state.get("turn", ""),
    ]
    return "|".join(str(p) for p in parts)


def _post_session(session: dict, proxy_url: str, player_kind: str) -> bool:
    payload = {
        "session_id": session["session_id"],
        "started_at": session["started_at"],
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "status": session["status"],
        "ending_type": session.get("ending_type"),
        "final_score": session.get("final_score"),
        "final_o2": session.get("final_o2"),
        "final_morale": session.get("final_morale"),
        "player_kind": player_kind,
        "game_version": "develop",
        "command_history": session["command_history"],
        "transcript": session["transcript"],
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{proxy_url}/v1/sessions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, OSError) as exc:
        sys.stderr.write(f"DB ingest failed (silently OK): {exc}\n")
        return False


def run_playtest(
    *,
    model: str = DEFAULT_MODEL,
    max_turns: int = DEFAULT_MAX_TURNS,
    stuck_window: int = DEFAULT_STUCK_WINDOW,
    no_ingest: bool = False,
    proxy_url: str = DEFAULT_PROXY_URL,
    output_path: pathlib.Path | None = None,
) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.stderr.write(
            "ANTHROPIC_API_KEY not set. Set it in env or via the launcher.\n"
        )
        sys.exit(2)

    # Imported here so the module can be analyzed (e.g., by tests) without
    # the SDK installed.
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=api_key)
    bridge = GameBridge()

    play_session_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"Playtest {play_session_id} starting (model: {model})", flush=True)
    print(f"  started: {started_at}", flush=True)
    print(f"  max-turns: {max_turns}, stuck-window: {stuck_window}", flush=True)
    print(flush=True)

    messages: list[dict] = [
        {
            "role": "user",
            "content": "Begin.",
        }
    ]

    state_history: list[str] = []
    turn = 0
    total_input_tokens = 0
    total_output_tokens = 0
    current_session_id: str | None = None
    last_response_text = ""
    final_state: dict | None = None
    ending_type: str | None = None
    bailout_reason = "max-turns"

    transcript = ""
    command_history: list[str] = []

    try:
        while turn < max_turns:
            turn += 1
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS_SCHEMA,
                messages=messages,
            )

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                # Model emitted only text, no tool call. End the run; the
                # game cannot continue without a tool invocation.
                bailout_reason = "no-tool-call"
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tu in tool_uses:
                tool_name = tu.name
                tool_input = tu.input or {}

                if tool_name == "mirs_end_start_game":
                    result = bridge.start_game()
                    current_session_id = result.get("session_id")
                    last_response_text = result.get("opening_text", "")
                    final_state = result.get("state")
                    print(f"[turn {turn}] start_game", flush=True)
                elif tool_name == "mirs_end_send_command":
                    result = bridge.send_command(
                        tool_input.get("session_id", ""),
                        tool_input.get("command", ""),
                    )
                    last_response_text = result.get("response_text", "")
                    final_state = result.get("state")
                    cmd = tool_input.get("command", "")
                    print(f"[turn {turn}] send_command: {cmd!r}", flush=True)
                elif tool_name == "mirs_end_get_state":
                    result = bridge.get_state(tool_input.get("session_id", ""))
                    print(f"[turn {turn}] get_state", flush=True)
                elif tool_name == "mirs_end_export_transcript":
                    result = bridge.export_transcript(
                        tool_input.get("session_id", ""),
                    )
                    bailout_reason = "agent-exported"
                    print(f"[turn {turn}] export_transcript", flush=True)
                else:
                    result = {"error": f"unknown tool: {tool_name}"}

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu.id,
                        "content": json.dumps(result),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

            sig = _state_signature(final_state or {})
            state_history.append(sig)
            if len(state_history) >= stuck_window:
                recent = state_history[-stuck_window:]
                if len(set(recent)) == 1:
                    bailout_reason = "stuck-loop"
                    break

            if last_response_text and _is_ending(final_state or {}, last_response_text):
                if "Begin preparations" in last_response_text:
                    ending_type = "transmit"
                elif "suffocated" in last_response_text.lower():
                    ending_type = "suffocate"
                else:
                    ending_type = "completed"
                bailout_reason = "ending"
                break

            if bailout_reason == "agent-exported":
                break

        if current_session_id:
            try:
                export = bridge.export_transcript(current_session_id)
                transcript = export.get("transcript", "")
                command_history = export.get("command_history", [])
            except Exception as exc:
                sys.stderr.write(f"transcript export failed: {exc}\n")

    finally:
        bridge.close()

    final_score = (final_state or {}).get("score")
    final_o2 = (final_state or {}).get("o2")
    final_morale = (final_state or {}).get("morale")
    estimated_cost_usd = (
        total_input_tokens * 3 / 1_000_000
        + total_output_tokens * 15 / 1_000_000
    )

    summary = {
        "session_id": play_session_id,
        "started_at": started_at,
        "model": model,
        "turns": turn,
        "bailout_reason": bailout_reason,
        "ending_type": ending_type,
        "status": "completed" if bailout_reason == "ending" else "stuck"
        if bailout_reason == "stuck-loop"
        else "abandoned",
        "final_score": final_score,
        "final_o2": final_o2,
        "final_morale": final_morale,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "estimated_cost_usd": round(estimated_cost_usd, 4),
        "command_history": command_history,
        "transcript": transcript,
    }

    print(flush=True)
    print(
        f"Playtest {play_session_id} done: turns={turn}, "
        f"bailout={bailout_reason}, score={final_score}, "
        f"cost=${estimated_cost_usd:.4f}",
        flush=True,
    )

    if output_path:
        output_path.write_text(json.dumps(summary, indent=2))
        print(f"Transcript saved to {output_path}", flush=True)

    if not no_ingest:
        ok = _post_session(summary, proxy_url, f"agent:{model}")
        if ok:
            print("DB ingest: 1 row written", flush=True)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sandboxed AI playtest driver for MIR'S END."
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--stuck-window", type=int, default=DEFAULT_STUCK_WINDOW)
    parser.add_argument("--no-ingest", action="store_true")
    parser.add_argument("--proxy-url", default=DEFAULT_PROXY_URL)
    parser.add_argument("--output", type=pathlib.Path, default=None)
    args = parser.parse_args()

    run_playtest(
        model=args.model,
        max_turns=args.max_turns,
        stuck_window=args.stuck_window,
        no_ingest=args.no_ingest,
        proxy_url=args.proxy_url,
        output_path=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
