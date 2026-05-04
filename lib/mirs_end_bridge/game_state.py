"""Game-state reader for Mir's End.

Parses [MIRSEND ...] status lines emitted by the Inform 7 runtime and
returns a structured Python dict matching the GameState TypedDict.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .types import GameState


# Pattern to match MIRSEND status-line fields.
# The game emits lines like: [MIRSEND room=Command Module]
_MIRSEND_PATTERN = re.compile(r"\[MIRSEND\s+(\w+)=([^\]]*)\]")


def parse_mirsend(raw: str) -> dict[str, str]:
    """Extract key-value pairs from all [MIRSEND key=value] tokens in *raw*."""
    return {m.group(1): m.group(2) for m in _MIRSEND_PATTERN.finditer(raw)}


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


def _parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip())
    except (ValueError, TypeError):
        return default


def _parse_int_or_none(value: str) -> int | None:
    try:
        return int(value.strip())
    except (ValueError, TypeError):
        return None


def build_game_state(
    mirsend_raw: str,
    ship_state: dict[str, Any] | None = None,
    recent_transcript: str = "",
) -> GameState:
    """Build a GameState dict from raw MIRSEND text and an optional ship snapshot.

    Parameters
    ----------
    mirsend_raw:
        The raw text containing ``[MIRSEND ...]`` tokens.
    ship_state:
        A ship-state snapshot (as returned by ``getShipState()`` in JS).
        May be ``None`` if unavailable.
    recent_transcript:
        The last N paragraphs of game output for context.
    """
    fields = parse_mirsend(mirsend_raw)

    # Parse truth states: expects comma-separated key:bool pairs
    truth_states: dict[str, bool] = {}
    if "truthStates" in fields:
        for pair in fields["truthStates"].split(","):
            pair = pair.strip()
            if ":" in pair:
                k, v = pair.split(":", 1)
                truth_states[k.strip()] = _parse_bool(v)

    # Parse inventory: expects comma-separated list
    inventory: list[str] = []
    if "inventory" in fields:
        inventory = [
            item.strip()
            for item in fields["inventory"].split(",")
            if item.strip()
        ]

    return GameState(
        currentRoom=fields.get("room", "unknown"),
        inventory=inventory,
        truthStates=truth_states,
        resources={
            "o2": _parse_int(fields.get("o2", "100")),
            "morale": _parse_int(fields.get("morale", "100")),
            "dose": _parse_int_or_none(fields.get("dose", "")),
        },
        score=_parse_int(fields.get("score", "0")),
        turn=_parse_int(fields.get("turn", "0")),
        recentTranscript=recent_transcript,
        shipState=ship_state or {},
    )


def render_ship_state_for_argon(ship_state: dict[str, Any]) -> str:
    """Translate a ship-state JSON snapshot into prose for the station-AI prompt.

    Mirrors the logic of ``renderShipStateForArgon()`` in ``lib/ship-state.js``
    so the Python bridge produces identical prose context. No em-dashes.
    Fragmented rhythm. Ritual exactness.
    """
    s = ship_state
    lines: list[str] = []

    # ── Time block ──────────────────────────────────────────────────────
    mission = s.get("mission", {})
    elapsed = mission.get("elapsed_since_impact", "00:00:00")
    clock_utc = mission.get("clock_utc", "")
    if clock_utc:
        # Extract HH:MM from ISO timestamp
        time_part = clock_utc.split("T")[1] if "T" in clock_utc else "00:00"
        hours = time_part[:2]
        minutes = time_part[3:5]
        elapsed_prose = _format_elapsed_prose(elapsed)
        lines.append(
            f"[Time onboard] Mission clock {hours}:{minutes} Moscow, "
            f"{elapsed_prose} since the impact."
        )

    # ── Orbit block ─────────────────────────────────────────────────────
    orbit = s.get("orbit", {})
    alt = orbit.get("altitude_km", 352)
    alt_text = _number_to_words(alt)
    region = orbit.get("region", "").replace("over ", "")
    lit = orbit.get("lit_side", True)
    lit_text = "Sunlit side" if lit else "Shadow side"
    terminator_s = orbit.get("time_to_terminator_s", 0)
    if terminator_s > 0:
        terminator_text = (
            f"{lit_text} for another {round(terminator_s / 60)} minutes."
        )
    else:
        terminator_text = f"{lit_text}. Terminator crossing imminent."
    lines.append(
        f"[Where we are] {alt_text} kilometres up. "
        f"Crossing {region} eastbound. {terminator_text}"
    )

    # ── Systems block ───────────────────────────────────────────────────
    lines.append("[My systems]")

    # Reactor
    reactor = s.get("reactor", {})
    pumps = reactor.get("coolant_pumps", {"running": 2, "total": 3})
    pump_text = _build_pump_text(pumps)
    lines.append(
        f"  Reactor: {reactor.get('state', 'idled')}. {pump_text} "
        f"Core temperature {reactor.get('core_temp', 'nominal')}. "
        f"Radiation output {reactor.get('rad_output_mSvh', 0.003)} mSv/h."
    )

    # Life support
    ls = s.get("life_support", {})
    temp_text = _format_temperature(
        ls.get("temperature", "nominal"),
        ls.get("temp_direction", "stable"),
    )
    o2_text = ls.get("o2_generator", "offline")
    lioh = ls.get("lioh_mode", "passive")
    lioh_text = (
        "LiOH active scrubbing" if lioh == "active" else "LiOH passive is holding"
    )
    co2_text = f"CO2 is {ls.get('co2_trend', 'stable')}"
    lines.append(
        f"  Life support: O2 generator {o2_text}. {lioh_text}. {co2_text}. "
        f"The temperature is {temp_text}. "
        f"Water recycler {ls.get('water_recycler', 'online')}."
    )

    # Power
    power = s.get("power", {})
    main_text = f"Main power: {power.get('main_bus', 'offline')}"
    bus_text = ""
    isolated = power.get("isolated_bus", {})
    if isolated.get("state") == "online":
        feeds = isolated.get("feeds", [])
        bus_text = f". One isolated bus is live, feeding {' and '.join(feeds)}"
    armored = power.get("armored_bus", "offline")
    armored_text = f". Armored bus {armored}" if armored != "offline" else ""
    lines.append(f"  {main_text}{bus_text}{armored_text}.")

    # Comms
    comms = s.get("comms", {})
    lines.append(
        f"  Comms array: {comms.get('array', 'offline')}. "
        f"Signal floor: {comms.get('signal_floor', 'static')}."
    )
    for name, info in comms.get("contacts", {}).items():
        display_name = name.replace("_", " ")
        parts: list[str] = []
        if info.get("last_heard"):
            parts.append(info["last_heard"])
        if info.get("live_channel"):
            parts.append("live channel open")
        if info.get("caretaker_mode"):
            parts.append("caretaker mode")
        if info.get("assumed_lost"):
            parts.append("assumed lost")
        if info.get("carrier") is False and not info.get("assumed_lost"):
            parts.append("no carrier")
        lines.append(
            f"    {display_name[0].upper()}{display_name[1:]}: "
            f"{'. '.join(parts)}."
        )

    # Hull
    hull = s.get("hull", {})
    lines.append(
        f"  Hull: central node {hull.get('central_node', 'nominal')}. "
        f"Other modules {hull.get('other_modules', 'nominal')}."
    )

    # Armament
    arm = s.get("armament", {})
    lines.append(
        f"  Armament: bay hatch {arm.get('bay_hatch', 'locked')}. "
        f"Fire control {arm.get('fire_control', 'offline')}. "
        f"{arm.get('shells_remaining', 0)} shells remaining."
    )

    # Propulsion
    prop = s.get("propulsion", {})
    lines.append(
        f"  Propulsion: {prop.get('fuel_pct', 0)} percent fuel. "
        f"Engine {prop.get('engine', 'cold')}. "
        f"{prop.get('delta_v_available_mps', 0)} m/s delta-v available."
    )

    # Docked
    docked = s.get("docked", {})
    lines.append(
        f"  Docked: Soyuz {docked.get('soyuz', 'nominal')}. "
        f"Progress {docked.get('progress', 'nominal')}."
    )

    # Crew
    crew = s.get("crew", {})
    alive_text = ", ".join(crew.get("known_alive", []))
    dead = crew.get("known_dead", [])
    dead_text = ", ".join(dead) if dead else "none confirmed"
    lines.append(f"  Crew: alive {alive_text}. Dead: {dead_text}.")
    unknown = crew.get("unknown", [])
    if unknown:
        lines.append(f"    Unaccounted: {', '.join(unknown)}.")

    return "\n".join(lines)


# ── Prose helpers (mirroring lib/ship-state.js) ─────────────────────────────


def _format_elapsed_prose(elapsed: str) -> str:
    parts = elapsed.split(":")
    h = int(parts[0]) if len(parts) > 0 else 0
    m = int(parts[1]) if len(parts) > 1 else 0
    pieces: list[str] = []
    if h > 0:
        pieces.append(f"{h} hour{'s' if h != 1 else ''}")
    if m > 0:
        pieces.append(f"{m} minute{'s' if m != 1 else ''}")
    return " and ".join(pieces) if pieces else "moments"


_HUNDRED_WORDS = [
    "", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine",
]
_TENS_WORDS = [
    "", "", "twenty", "thirty", "forty",
    "fifty", "sixty", "seventy", "eighty", "ninety",
]
_ONES_WORDS = [
    "", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]


def _number_to_words(n: int) -> str:
    hundreds = n // 100
    remainder = n % 100
    result = ""
    if hundreds > 0:
        result += f"{_HUNDRED_WORDS[hundreds]} hundred"
    if remainder > 0:
        if result:
            result += " "
        if remainder < 20:
            result += _ONES_WORDS[remainder]
        else:
            tens = remainder // 10
            ones = remainder % 10
            result += _TENS_WORDS[tens]
            if ones > 0:
                result += f"-{_ONES_WORDS[ones]}"
    return result[0].upper() + result[1:] if result else str(n)


def _build_pump_text(pumps: dict) -> str:
    running = pumps.get("running", 0)
    total = pumps.get("total", 3)
    if running == 0:
        return "All coolant pumps stopped."
    if running == total:
        return f"All {total} coolant pumps running."
    stopped = total - running
    r_word = _number_word_small(running)
    s_word = _number_word_small(stopped)
    r_suffix = "s" if running != 1 else ""
    s_verb = "ve" if stopped != 1 else "s"
    return (
        f"{r_word[0].upper()}{r_word[1:]} coolant pump{r_suffix} still running. "
        f"{s_word[0].upper()}{s_word[1:]} ha{s_verb} stopped."
    )


def _number_word_small(n: int) -> str:
    words = [
        "zero", "one", "two", "three", "four",
        "five", "six", "seven", "eight", "nine",
    ]
    return words[n] if n < len(words) else str(n)


def _format_temperature(bucket: str, direction: str) -> str:
    if direction in ("stable", "") or direction is None:
        return bucket
    return f"{bucket} and {direction}"
