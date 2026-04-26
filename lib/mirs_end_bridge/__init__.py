"""Mir's End LLM Bridge
====================

Shared library that every LLM-consuming component in the Mir's End project
depends on.  Sits between the game and Claude.

Modules
-------
game_state
    Parses ``[MIRSEND ...]`` status lines and translates ship-state JSON into
    prose via ``render_ship_state_for_argon()``.
prompts
    Composes complete prompts (system + messages) for any role:
    ``"station-ai"``, ``"director"``, ``"narrator"``, ``"player"``.
voice_kit
    Loads and caches the writing-sample and persona markdown files that
    define the narrative voice.
claude
    Thin wrapper around the Anthropic SDK with retry on 429, per-call cost
    accounting, and typed responses.
logs
    Append-only JSONL transcript logger for every Claude call.
sanitize
    Input sanitization: length cap, control-char stripping, suspicious-
    pattern rejection, and XML escaping for ``<player_speech>`` blocks.
guardrails
    Post-hoc frame-break detection and incident logging.
types
    ``GameState``, ``Prompt``, ``LLMResponse``, ``CostReport`` type
    definitions.

Quick start
-----------
::

    from mirs_end_bridge.game_state import build_game_state, render_ship_state_for_argon
    from mirs_end_bridge.prompts import compose_prompt
    from mirs_end_bridge.claude import call_claude, get_cost_report

    state = build_game_state(mirsend_raw, ship_snapshot)
    prompt = compose_prompt("station-ai", state, player_utterance="Hello?")
    response = call_claude(prompt)
    print(response.text, response.cost_usd)
"""

from .types import CostReport, GameState, LLMResponse, Prompt

__all__ = [
    "CostReport",
    "GameState",
    "LLMResponse",
    "Prompt",
]
