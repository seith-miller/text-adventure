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
  --file-bugs            Add a `report_bug` tool to the agent's catalog. When
                         called, files a GitHub issue (labels: playtest, bug)
                         and stops the playtest. Default off — opt in for
                         scheduled QA runs and CI.

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

# Appended to SYSTEM_PROMPT when --file-bugs is on. Kept in a separate
# constant so the default (sandboxed, no-file) prompt stays one sentence.
BUG_FILING_ADDENDUM = (
    " You also have a `report_bug` tool. Call it ONLY when you observe a real,"
    " reproducible bug — a wrong response, broken puzzle logic, contradictory"
    " state, parser inconsistency, or anything that would make a developer say"
    " 'yes that's wrong'. Do NOT report things you simply don't enjoy or don't"
    " understand. When in doubt, keep playing. Calling report_bug stops the"
    " playtest."
)

# Optional 5th tool, only attached when --file-bugs is on. Mirrors the
# UI harness's report_bug schema so triagers see consistent issue shape.
REPORT_BUG_TOOL = {
    "name": "report_bug",
    "description": (
        "Report a real, reproducible bug. Stops the playtest. Use only when "
        "you've observed something that would qualify as a defect to a "
        "developer — not aesthetic preference, not narrative confusion."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Brief bug title (under 80 chars)",
            },
            "description": {
                "type": "string",
                "description": (
                    "Markdown reproduction: commands you sent, what the game "
                    "responded with, what was wrong, what you expected. "
                    "Include enough that a developer can reproduce from your "
                    "description alone."
                ),
            },
            "severity": {
                "type": "string",
                "enum": ["minor", "moderate", "severe"],
                "description": (
                    "minor=cosmetic prose drift, moderate=functional but "
                    "recoverable, severe=blocks gameplay or corrupts state"
                ),
            },
        },
        "required": ["title", "description", "severity"],
    },
}

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
    if "mirs_end_mcp" in sys.modules:
        return sys.modules["mirs_end_mcp"]
    spec = importlib.util.spec_from_file_location(
        "mirs_end_mcp", str(REPO_ROOT / "scripts" / "mirs_end_mcp.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load mirs_end_mcp module")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # required by Python 3.14 dataclass lookup
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
            await self._backend.shutdown()

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


_CACHE_CONTROL = {"type": "ephemeral"}


def _strip_cache_control(messages: list[dict]) -> list[dict]:
    """Return messages with any cache_control markers removed."""
    cleaned = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            new_content = []
            for block in content:
                if isinstance(block, dict) and "cache_control" in block:
                    block = {k: v for k, v in block.items() if k != "cache_control"}
                new_content.append(block)
            cleaned.append({**msg, "content": new_content})
        else:
            cleaned.append(msg)
    return cleaned


def _with_cache_breakpoint(messages: list[dict]) -> list[dict]:
    """
    Drop any prior cache_control markers and add one to the last block of
    the last message. This caches the conversation prefix as it grows so
    subsequent turns pay 0.1x for re-sent context.
    """
    cleaned = _strip_cache_control(messages)
    if not cleaned:
        return cleaned
    last = cleaned[-1]
    content = last["content"]
    if isinstance(content, str):
        new_content = [
            {"type": "text", "text": content, "cache_control": _CACHE_CONTROL}
        ]
    else:
        new_content = list(content)
        for i in range(len(new_content) - 1, -1, -1):
            block = new_content[i]
            if isinstance(block, dict):
                new_content[i] = {**block, "cache_control": _CACHE_CONTROL}
                break
    cleaned[-1] = {**last, "content": new_content}
    return cleaned


def _tools_with_cache(tools: list[dict]) -> list[dict]:
    """Return tools with cache_control on the last entry to lock the static prefix."""
    if not tools:
        return tools
    out = [dict(t) for t in tools]
    out[-1] = {**out[-1], "cache_control": _CACHE_CONTROL}
    return out


def _system_with_cache(prompt: str) -> list[dict]:
    return [{"type": "text", "text": prompt, "cache_control": _CACHE_CONTROL}]


def _read_game_version() -> str:
    """
    Return the version descriptor produced by scripts/make_version.py.

    Falls back to "unknown" if the file is missing or unreadable.
    """
    path = REPO_ROOT / "game" / "dist" / "version.json"
    try:
        data = json.loads(path.read_text())
        v = data.get("version_string")
        if isinstance(v, str) and v.strip():
            return v.strip()
    except (OSError, ValueError):
        pass
    return "unknown"


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
        "game_version": session.get("game_version") or _read_game_version(),
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


DEFAULT_DUMP_DIR = REPO_ROOT / "docs" / "playtests" / "runs"


def _file_bug_to_github(
    *,
    title: str,
    description: str,
    severity: str,
    model: str,
    play_session_id: str,
    turn: int,
    transcript: str,
    command_history: list[str],
    final_state: dict | None,
    milestone: str | None = None,
    dry_run: bool = False,
) -> str | None:
    """
    Run `gh issue create` to file a bug found by the playtester. Returns
    the resulting issue URL on success, None if filing failed or dry_run.
    Mirrors the issue shape produced by scripts/playtest-with-ui.mjs so
    triagers see a consistent format from both harnesses.
    """
    import subprocess  # noqa: PLC0415

    body_lines = [
        f"## Severity\n{severity}",
        "",
        "## Description",
        description,
        "",
        "## How it was found",
        (
            f"Filed by `scripts/playtest.py` ({model}) after {turn} turns. "
            f"Session id: `{play_session_id}`. The text-only harness drives "
            f"Glulx via MCP and does not see the rendered UI."
        ),
        "",
        "## Final state",
        f"```json\n{json.dumps(final_state or {}, indent=2)}\n```",
        "",
        "## Commands the agent submitted",
        "```",
        "\n".join(command_history) or "(none)",
        "```",
        "",
        "<details><summary>Full transcript</summary>",
        "",
        "```",
        transcript or "(empty)",
        "```",
        "",
        "</details>",
    ]
    body = "\n".join(body_lines)

    print(f"\n[playtest] BUG REPORTED ({severity}): {title}", flush=True)

    if dry_run:
        print("[playtest] --no-file-only: would have created issue", flush=True)
        print(f"[playtest] body:\n{body[:1000]}…", flush=True)
        return None

    args = [
        "gh", "issue", "create",
        "--title", f"[playtest] {title}",
        "--body", body,
        "--label", "playtest,bug",
    ]
    if milestone:
        args.extend(["--milestone", milestone])

    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        sys.stderr.write("gh CLI not on PATH; cannot file bug\n")
        return None
    if result.returncode != 0:
        sys.stderr.write(f"gh issue create failed: {result.stderr}\n")
        return None
    url = result.stdout.strip()
    print(f"[playtest] filed: {url}", flush=True)
    return url


def run_playtest(
    *,
    model: str = DEFAULT_MODEL,
    max_turns: int = DEFAULT_MAX_TURNS,
    stuck_window: int = DEFAULT_STUCK_WINDOW,
    no_ingest: bool = False,
    proxy_url: str = DEFAULT_PROXY_URL,
    output_path: pathlib.Path | None = None,
    dump_dir: pathlib.Path | None = DEFAULT_DUMP_DIR,
    file_bugs: bool = False,
    bug_milestone: str | None = None,
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
    active_system = (
        SYSTEM_PROMPT + BUG_FILING_ADDENDUM if file_bugs else SYSTEM_PROMPT
    )
    active_tools = (
        TOOLS_SCHEMA + [REPORT_BUG_TOOL] if file_bugs else TOOLS_SCHEMA
    )
    print(f"Playtest {play_session_id} starting (model: {model})", flush=True)
    print(f"  started: {started_at}", flush=True)
    print(f"  max-turns: {max_turns}, stuck-window: {stuck_window}", flush=True)
    if file_bugs:
        print(
            f"  bug filing: ON (will file to GitHub on report_bug call"
            f"{', milestone=' + bug_milestone if bug_milestone else ''})",
            flush=True,
        )
    print(flush=True)

    messages: list[dict] = [
        {
            "role": "user",
            "content": "Begin.",
        }
    ]

    state_history: list[str] = []
    turn = 0
    game_turn = 0  # counts only mirs_end_send_command turns
    consecutive_no_tool = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cache_creation_tokens = 0
    total_cache_read_tokens = 0
    current_session_id: str | None = None
    last_response_text = ""
    final_state: dict | None = None
    ending_type: str | None = None
    bailout_reason = "max-turns"

    transcript = ""
    command_history: list[str] = []
    turns_log: list[dict] = []
    stuck_moments: list[dict] = []

    try:
        while turn < max_turns:
            turn += 1
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=_system_with_cache(active_system),
                tools=_tools_with_cache(active_tools),
                messages=_with_cache_breakpoint(messages),
            )

            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens
            total_cache_creation_tokens += getattr(
                response.usage, "cache_creation_input_tokens", 0
            ) or 0
            total_cache_read_tokens += getattr(
                response.usage, "cache_read_input_tokens", 0
            ) or 0

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                # Model emitted only text. Sampling variance: sometimes
                # the model "thinks out loud" before its next tool call.
                # Append the text and a nudge, give it a few chances.
                consecutive_no_tool += 1
                if consecutive_no_tool >= 3:
                    bailout_reason = "no-tool-call"
                    break
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": "Continue playing the game by calling one of the available tools.",
                })
                print(f"[turn {turn}] text-only response; nudging", flush=True)
                continue
            consecutive_no_tool = 0

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
                    game_turn += 1
                    state_for_log = final_state or {}
                    turns_log.append(
                        {
                            "turn_number": game_turn,
                            "command": cmd,
                            "response": last_response_text,
                            "current_room": state_for_log.get("currentRoom"),
                            "inventory": state_for_log.get("inventory") or [],
                            "o2": state_for_log.get("o2"),
                            "morale": state_for_log.get("morale"),
                            "truth_states": None,
                        }
                    )
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
                elif tool_name == "report_bug" and file_bugs:
                    # Bug filing terminates the playtest — same convention
                    # as the UI harness. Capture the partial transcript
                    # before exiting the loop.
                    bug_title = str(tool_input.get("title", "(untitled)"))
                    bug_desc = str(tool_input.get("description", ""))
                    bug_severity = str(tool_input.get("severity", "minor"))
                    transcript_so_far = ""
                    cmd_history_so_far: list[str] = []
                    if current_session_id:
                        try:
                            export = bridge.export_transcript(current_session_id)
                            transcript_so_far = export.get("transcript", "")
                            cmd_history_so_far = export.get("command_history", [])
                        except Exception:
                            pass
                    bug_url = _file_bug_to_github(
                        title=bug_title,
                        description=bug_desc,
                        severity=bug_severity,
                        model=model,
                        play_session_id=play_session_id,
                        turn=game_turn,
                        transcript=transcript_so_far,
                        command_history=cmd_history_so_far,
                        final_state=final_state,
                        milestone=bug_milestone,
                    )
                    result = {
                        "filed": bool(bug_url),
                        "issue_url": bug_url,
                        "message": (
                            "Bug filed; playtest is stopping."
                            if bug_url
                            else "Bug logged locally; gh filing failed."
                        ),
                    }
                    bailout_reason = "bug-reported"
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
                    room = (final_state or {}).get("currentRoom") or "unknown"
                    stuck_moments.append(
                        {
                            "turn_start": max(1, game_turn - stuck_window + 1),
                            "turn_end": game_turn,
                            "room": room,
                            "window": stuck_window,
                        }
                    )
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

            if bailout_reason in ("agent-exported", "bug-reported"):
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
    # Sonnet 4.5 pricing: input $3/Mtok, cache write $3.75/Mtok (1.25x),
    # cache read $0.30/Mtok (0.1x), output $15/Mtok.
    estimated_cost_usd = (
        total_input_tokens * 3 / 1_000_000
        + total_cache_creation_tokens * 3.75 / 1_000_000
        + total_cache_read_tokens * 0.30 / 1_000_000
        + total_output_tokens * 15 / 1_000_000
    )

    status = (
        "completed" if bailout_reason == "ending"
        else "stuck" if bailout_reason == "stuck-loop"
        else "abandoned"
    )

    metadata = {
        "bailout_reason": bailout_reason,
        "input_tokens": str(total_input_tokens),
        "output_tokens": str(total_output_tokens),
        "cache_creation_tokens": str(total_cache_creation_tokens),
        "cache_read_tokens": str(total_cache_read_tokens),
        "estimated_cost_usd": f"{estimated_cost_usd:.4f}",
        "model": model,
    }
    if stuck_moments:
        metadata["stuck_moments"] = json.dumps(stuck_moments)

    summary = {
        "session_id": play_session_id,
        "started_at": started_at,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "turns_count": turn,
        "bailout_reason": bailout_reason,
        "ending_type": ending_type,
        "status": status,
        "final_score": final_score,
        "final_o2": final_o2,
        "final_morale": final_morale,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "cache_creation_tokens": total_cache_creation_tokens,
        "cache_read_tokens": total_cache_read_tokens,
        "estimated_cost_usd": round(estimated_cost_usd, 4),
        "command_history": command_history,
        "transcript": transcript,
        "turns": turns_log,
        "stuck_moments": stuck_moments,
        "metadata": metadata,
        "player_kind": f"agent:{model}",
        "game_version": _read_game_version(),
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

    if dump_dir is not None:
        try:
            sys.path.insert(0, str(REPO_ROOT))
            from lib.playthrough_db import format_session_markdown  # noqa: PLC0415
            dump_dir.mkdir(parents=True, exist_ok=True)
            date_part = (summary.get("started_at") or "")[:10] or "undated"
            md_path = dump_dir / f"{date_part}-{play_session_id}.md"
            md_path.write_text(format_session_markdown(summary))
            print(f"Markdown transcript: {md_path}", flush=True)
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write(f"Markdown dump failed (non-fatal): {exc}\n")

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
    parser.add_argument(
        "--dump-dir", type=pathlib.Path, default=DEFAULT_DUMP_DIR,
        help="Directory for the auto-dumped markdown transcript "
             "(default: docs/playtests/runs/).",
    )
    parser.add_argument(
        "--no-dump", action="store_true",
        help="Suppress the markdown auto-dump entirely.",
    )
    parser.add_argument(
        "--file-bugs", action="store_true",
        help=(
            "Add a `report_bug` tool to the agent's catalog and file any "
            "reports as GitHub issues with `playtest` + `bug` labels. "
            "Default off — opt in for scheduled QA runs and CI."
        ),
    )
    parser.add_argument(
        "--bug-milestone", default=None,
        help=(
            "Optional GitHub milestone to attach to filed bugs. Off by "
            "default since the playtester finds any kind of real bug and a "
            "static milestone would mis-tag most of them."
        ),
    )
    args = parser.parse_args()

    run_playtest(
        model=args.model,
        max_turns=args.max_turns,
        stuck_window=args.stuck_window,
        no_ingest=args.no_ingest,
        dump_dir=None if args.no_dump else args.dump_dir,
        proxy_url=args.proxy_url,
        output_path=args.output,
        file_bugs=args.file_bugs,
        bug_milestone=args.bug_milestone,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
