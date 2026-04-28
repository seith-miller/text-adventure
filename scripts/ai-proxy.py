#!/usr/bin/env python3
"""Mir's End — Local AI Proxy Server

Thin HTTP proxy that holds the Anthropic API key server-side and forwards
prompts from browser-side consumers (the in-game Argon-87 runtime).

Launch:
    python scripts/ai-proxy.py

Requires ANTHROPIC_API_KEY environment variable to be set.
Listens on localhost:8787 by default.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Ensure the lib directory is importable.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "lib"))

from mirs_end_bridge.claude import BridgeAPIError, call_claude
from mirs_end_bridge.game_state import build_game_state
from mirs_end_bridge.logs import log_call
from mirs_end_bridge.prompts import compose_prompt
from mirs_end_bridge.types import LLMResponse

# Re-import write_session from playthrough_db for the /v1/sessions route.
sys.path.insert(0, str(_PROJECT_ROOT))
from lib.playthrough_db import write_session  # noqa: E402

# ── Configuration ────────────────────────────────────────────────────────────

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
ALLOWED_ORIGIN = os.environ.get("AI_PROXY_ALLOWED_ORIGIN", "http://localhost:8080")
RATE_LIMIT_PER_MINUTE = int(os.environ.get("AI_PROXY_RATE_LIMIT", "30"))
VALID_ROLES = {"station-ai", "director", "narrator"}

# ── Logging (never log the API key) ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("ai-proxy")

# ── Rate limiter (simple in-memory, per-origin) ─────────────────────────────

_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(origin: str) -> bool:
    """Return True if the request is within the rate limit."""
    now = time.time()
    window_start = now - 60.0
    timestamps = _rate_store[origin]
    # Prune old entries.
    _rate_store[origin] = [t for t in timestamps if t > window_start]
    if len(_rate_store[origin]) >= RATE_LIMIT_PER_MINUTE:
        return False
    _rate_store[origin].append(now)
    return True


# ── Request / response models ────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    role: str
    content: str


class CallRequest(BaseModel):
    role: str
    game_state: dict[str, Any]
    player_input: str
    conversation_history: list[ConversationMessage] = Field(default_factory=list)


class UsageInfo(BaseModel):
    input_tokens: int
    output_tokens: int
    cost_usd: float


class CallResponse(BaseModel):
    response: str
    usage: UsageInfo


# ── App lifecycle ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify API key is set on startup."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY is not set. Refusing to start.")
        sys.exit(1)
    logger.info("AI proxy starting on %s:%s", DEFAULT_HOST, DEFAULT_PORT)
    logger.info("Allowed origin: %s", ALLOWED_ORIGIN)
    yield
    logger.info("AI proxy shutting down.")


# ── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="Mir's End AI Proxy", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# ── Origin check middleware ──────────────────────────────────────────────────

@app.middleware("http")
async def origin_check(request: Request, call_next):
    """Reject non-OPTIONS requests without a valid Origin header."""
    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path == "/health":
        return await call_next(request)

    origin = request.headers.get("origin", "")
    if origin != ALLOWED_ORIGIN:
        logger.warning("Rejected request from origin: %s", origin or "(none)")
        return JSONResponse(
            status_code=403,
            content={"detail": "Origin not allowed"},
        )

    if not _check_rate_limit(origin):
        logger.warning("Rate limit exceeded for origin: %s", origin)
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again in a minute."},
        )

    return await call_next(request)


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/v1/call", response_model=CallResponse)
async def call_llm(body: CallRequest):
    """Forward a prompt to Claude via the shared bridge."""
    # Validate role.
    if body.role not in VALID_ROLES:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Invalid role: {body.role}. Must be one of: {', '.join(sorted(VALID_ROLES))}"},
        )

    try:
        # Build game state from the request payload.
        game_state = build_game_state(
            mirsend_raw="",
            ship_state=body.game_state.get("shipState", body.game_state),
            recent_transcript=body.game_state.get("recentTranscript", ""),
        )
        # Override fields that came directly from the browser.
        game_state["currentRoom"] = body.game_state.get("currentRoom", game_state["currentRoom"])
        game_state["inventory"] = body.game_state.get("inventory", game_state["inventory"])
        game_state["score"] = body.game_state.get("score", game_state["score"])
        game_state["turn"] = body.game_state.get("turn", game_state["turn"])
        if "resources" in body.game_state:
            game_state["resources"] = body.game_state["resources"]
        if "truthStates" in body.game_state:
            game_state["truthStates"] = body.game_state["truthStates"]

        # Build conversation history as extra context.
        history_text = ""
        if body.conversation_history:
            parts = []
            for msg in body.conversation_history:
                label = "Player" if msg.role == "player" else "Argon-87"
                parts.append(f"{label}: {msg.content}")
            history_text = "\n".join(parts)

        # Compose the prompt via the bridge.
        prompt = compose_prompt(
            role=body.role,
            game_state=game_state,
            player_utterance=body.player_input,
            extra_context=f"## Conversation history\n\n{history_text}" if history_text else "",
        )

        # Call Claude.
        result: LLMResponse = call_claude(prompt)

        logger.info(
            "Claude call complete: role=%s, tokens_in=%d, tokens_out=%d, cost=$%.5f",
            body.role,
            result.input_tokens,
            result.output_tokens,
            result.cost_usd,
        )

        return CallResponse(
            response=result.text,
            usage=UsageInfo(
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
            ),
        )

    except BridgeAPIError as exc:
        logger.error("Bridge API error: %s", exc)
        status = exc.status_code or 502
        return JSONResponse(
            status_code=status,
            content={"detail": f"LLM call failed: {exc}"},
        )
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


# ── Session ingest ──────────────────────────────────────────────────────────


def _normalize_session_payload(body: dict) -> dict:
    """
    Translate the various session payload shapes the project sends into
    the schema ``playthrough_db.write_session`` expects.

    Three callers send to /v1/sessions:
      - browser ui.js: ``turns`` is an int (count), ``final_state`` dict,
        ``command_history`` list of strings, ``transcript`` joined string
      - scripts/playtest.py: flat ``final_o2``/``final_morale``/``final_score``,
        ``command_history`` list of strings, ``transcript`` joined string
      - scripts/playtest-pool.py worker (currently bypasses HTTP): ``turns``
        list of full per-turn dicts

    All paths share ``session_id``, ``started_at``, ``status``, etc.
    """
    sid = body.get("session_id")
    if not isinstance(sid, str) or not sid:
        raise ValueError("session_id is required and must be a non-empty string")

    turns_in = body.get("turns")
    if isinstance(turns_in, list):
        turns = turns_in
    else:
        turns = []
        for i, cmd in enumerate(body.get("command_history") or [], start=1):
            turns.append({"turn_number": i, "command": cmd, "response": None})

    fs = body.get("final_state") or {}

    def _pick(*keys, default=None):
        for k in keys:
            if k in body and body[k] is not None:
                return body[k]
        return default

    return {
        "session_id": sid,
        "started_at": body.get("started_at"),
        "ended_at": body.get("ended_at"),
        "status": body.get("status", "in_progress"),
        "ending_type": body.get("ending_type"),
        "final_score": _pick("final_score", default=fs.get("score")),
        "final_o2": _pick("final_o2", default=fs.get("o2")),
        "final_morale": _pick("final_morale", default=fs.get("morale")),
        "player_kind": body.get("player_kind", "unknown"),
        "game_version": body.get("game_version", "unknown"),
        "notes": body.get("notes"),
        "turns": turns,
        "metadata": body.get("metadata") or {},
    }


@app.post("/v1/sessions")
async def ingest_session(body: dict):
    """
    Persist a playthrough to ``data/playthroughs.sqlite``.

    Accepts payload shapes from the browser, the playtest CLI driver, and
    the pool runner; normalizes them and calls ``write_session``. Idempotent
    on ``session_id``.
    """
    try:
        payload = _normalize_session_payload(body)
        counts = write_session(payload)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except Exception as exc:  # noqa: BLE001
        logger.error("Session ingest failed: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Session ingest failed: {exc}"},
        )

    logger.info(
        "Session ingest: id=%s player=%s status=%s turns=%d",
        payload["session_id"],
        payload["player_kind"],
        payload["status"],
        counts.get("turns", 0),
    )
    return {"ok": True, "counts": counts}


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    """Start the proxy server."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY is not set. Refusing to start.")
        sys.exit(1)

    host = os.environ.get("AI_PROXY_HOST", DEFAULT_HOST)
    port = int(os.environ.get("AI_PROXY_PORT", str(DEFAULT_PORT)))

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
