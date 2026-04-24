"""Prompt composer for Mir's End.

Takes a role, game state, and application-specific context and returns a
complete Prompt (system message + messages list) ready for the Claude API.
"""

from __future__ import annotations

from .game_state import render_ship_state_for_argon
from .types import GameState, Prompt
from .voice_kit import get_voice_kit


def compose_prompt(
    role: str,
    game_state: GameState,
    *,
    player_utterance: str = "",
    scene_label: str = "",
    extra_context: str = "",
) -> Prompt:
    """Build a complete prompt for the given *role*.

    Parameters
    ----------
    role:
        One of ``"station-ai"``, ``"director"``, ``"narrator"``, ``"player"``.
    game_state:
        A GameState dict with current room, inventory, ship state, etc.
    player_utterance:
        What the player just said (relevant for station-ai and director).
    scene_label:
        Current scene label for narrator/director roles.
    extra_context:
        Any additional context the caller wants injected.
    """
    kit = get_voice_kit(role)
    system_parts: list[str] = []

    # ── System prompt ───────────────────────────────────────────────────
    if role == "station-ai":
        system_parts.append(kit["station_ai_persona"])
    else:
        system_parts.append(f"You are the {role} for Mir's End.")
        system_parts.append(kit["writing_style"])

    # ── Voice samples (all roles) ───────────────────────────────────────
    system_parts.append(
        "## Voice samples\n\n"
        "### Darkling Beetles (mystic register)\n\n"
        f"{kit['darkling_beetles']}\n\n"
        "### The Man, Ava (elemental register)\n\n"
        f"{kit['the_man_ava']}"
    )

    # ── Game-state block ────────────────────────────────────────────────
    ship_state = game_state.get("shipState", {})
    if ship_state:
        prose_state = render_ship_state_for_argon(ship_state)
    else:
        prose_state = "(Ship state unavailable.)"

    state_block = (
        "## Current game state\n\n"
        f"Room: {game_state['currentRoom']}\n"
        f"Turn: {game_state['turn']}\n"
        f"Score: {game_state['score']}\n"
        f"Inventory: {', '.join(game_state['inventory']) or 'empty'}\n"
        f"O2: {game_state['resources']['o2']}  "
        f"Morale: {game_state['resources']['morale']}  "
        f"Dose: {game_state['resources'].get('dose', 'N/A')}\n\n"
        f"### Ship status (prose)\n\n{prose_state}"
    )
    system_parts.append(state_block)

    if extra_context:
        system_parts.append(f"## Additional context\n\n{extra_context}")

    system = "\n\n".join(system_parts)

    # ── Messages (user turn) ────────────────────────────────────────────
    messages: list[dict[str, str]] = []

    if game_state.get("recentTranscript"):
        messages.append({
            "role": "user",
            "content": (
                f"[Recent game transcript]\n{game_state['recentTranscript']}"
            ),
        })
        messages.append({
            "role": "assistant",
            "content": "Understood. I have the transcript context.",
        })

    user_content_parts: list[str] = []
    if scene_label:
        user_content_parts.append(f"[Scene: {scene_label}]")
    if player_utterance:
        user_content_parts.append(player_utterance)
    elif not scene_label:
        user_content_parts.append("(Awaiting input.)")

    messages.append({"role": "user", "content": "\n".join(user_content_parts)})

    return Prompt(system=system, messages=messages)
