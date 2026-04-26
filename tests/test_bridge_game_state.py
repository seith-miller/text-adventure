"""Tests for mirs_end_bridge.game_state."""

import pytest

from mirs_end_bridge.game_state import (
    build_game_state,
    parse_mirsend,
    render_ship_state_for_argon,
)


class TestParseMirsend:
    def test_single_field(self):
        raw = "[MIRSEND room=Command Module]"
        assert parse_mirsend(raw) == {"room": "Command Module"}

    def test_multiple_fields(self):
        raw = (
            "[MIRSEND room=Reactor Bay] some text "
            "[MIRSEND turn=5] [MIRSEND score=10]"
        )
        result = parse_mirsend(raw)
        assert result["room"] == "Reactor Bay"
        assert result["turn"] == "5"
        assert result["score"] == "10"

    def test_no_mirsend(self):
        assert parse_mirsend("Just regular game text.") == {}

    def test_inventory_field(self):
        raw = "[MIRSEND inventory=wrench,dosimeter,keycard]"
        result = parse_mirsend(raw)
        assert result["inventory"] == "wrench,dosimeter,keycard"


class TestBuildGameState:
    def test_basic_parsing(self):
        raw = (
            "[MIRSEND room=Command Module] [MIRSEND turn=3] "
            "[MIRSEND score=15] [MIRSEND o2=85] [MIRSEND morale=70] "
            "[MIRSEND inventory=wrench,dosimeter]"
        )
        state = build_game_state(raw)
        assert state["currentRoom"] == "Command Module"
        assert state["turn"] == 3
        assert state["score"] == 15
        assert state["resources"]["o2"] == 85
        assert state["resources"]["morale"] == 70
        assert state["inventory"] == ["wrench", "dosimeter"]

    def test_defaults(self):
        state = build_game_state("")
        assert state["currentRoom"] == "unknown"
        assert state["turn"] == 0
        assert state["score"] == 0
        assert state["inventory"] == []
        assert state["shipState"] == {}

    def test_truth_states(self):
        raw = "[MIRSEND truthStates=power-is-restored:true,reactor-scrammed:false]"
        state = build_game_state(raw)
        assert state["truthStates"]["power-is-restored"] is True
        assert state["truthStates"]["reactor-scrammed"] is False

    def test_ship_state_passthrough(self):
        ship = {"mission": {"turn": 5}}
        state = build_game_state("", ship_state=ship)
        assert state["shipState"] == ship

    def test_recent_transcript(self):
        state = build_game_state("", recent_transcript="You enter the module.")
        assert state["recentTranscript"] == "You enter the module."

    def test_dose_none(self):
        state = build_game_state("")
        assert state["resources"]["dose"] is None

    def test_dose_present(self):
        raw = "[MIRSEND dose=42]"
        state = build_game_state(raw)
        assert state["resources"]["dose"] == 42


# A minimal default ship-state fixture matching lib/ship-state.js defaults.
DEFAULT_SHIP_STATE = {
    "mission": {
        "turn": 0,
        "clock_utc": "1987-10-24T03:01:27Z",
        "elapsed_since_impact": "00:00:00",
    },
    "orbit": {
        "altitude_km": 352,
        "inclination_deg": 51.6,
        "ground_track_lat": 51,
        "ground_track_lon": 37,
        "region": "over Russia (Moscow corridor)",
        "lit_side": True,
        "time_to_terminator_s": 1240,
    },
    "reactor": {
        "state": "idled",
        "coolant_pumps": {"running": 2, "total": 3},
        "core_temp": "nominal",
        "rad_output_mSvh": 0.003,
    },
    "life_support": {
        "o2_generator": "offline",
        "lioh_mode": "passive",
        "co2_trend": "rising slow",
        "temperature": "nominal",
        "temp_direction": "falling",
        "water_recycler": "online",
    },
    "power": {
        "main_bus": "offline",
        "isolated_bus": {
            "state": "online",
            "feeds": ["status_console", "comms_array"],
        },
        "armored_bus": "offline",
    },
    "comms": {
        "array": "patched to isolated bus",
        "signal_floor": "static",
        "contacts": {
            "freedom_station": {"last_heard": "distress loop", "live_channel": False},
            "selengrad": {"last_heard": "silent", "caretaker_mode": True},
            "baikonur": {"carrier": False, "assumed_lost": True},
        },
    },
    "hull": {
        "central_node": "breached, sealed",
        "other_modules": "nominal",
    },
    "armament": {
        "bay_hatch": "unlocked",
        "fire_control": "offline",
        "shells_remaining": 3,
    },
    "propulsion": {
        "fuel_pct": 78,
        "engine": "cold",
        "delta_v_available_mps": 340,
    },
    "docked": {
        "soyuz": "nominal",
        "progress": "battery intact",
    },
    "crew": {
        "known_alive": ["self"],
        "known_dead": ["Kozlova", "Petrov"],
        "unknown": [],
    },
}


class TestRenderShipStateForArgon:
    def test_produces_time_block(self):
        prose = render_ship_state_for_argon(DEFAULT_SHIP_STATE)
        assert "[Time onboard]" in prose
        assert "03:01 Moscow" in prose
        assert "since the impact" in prose

    def test_produces_orbit_block(self):
        prose = render_ship_state_for_argon(DEFAULT_SHIP_STATE)
        assert "[Where we are]" in prose
        assert "kilometres up" in prose
        assert "Russia (Moscow corridor)" in prose

    def test_produces_systems_block(self):
        prose = render_ship_state_for_argon(DEFAULT_SHIP_STATE)
        assert "[My systems]" in prose
        assert "Reactor: idled" in prose
        assert "coolant pump" in prose

    def test_no_em_dashes(self):
        prose = render_ship_state_for_argon(DEFAULT_SHIP_STATE)
        assert "\u2014" not in prose, "Prose must not contain em-dashes"

    def test_crew_section(self):
        prose = render_ship_state_for_argon(DEFAULT_SHIP_STATE)
        assert "alive self" in prose
        assert "Dead: Kozlova, Petrov" in prose

    def test_comms_contacts(self):
        prose = render_ship_state_for_argon(DEFAULT_SHIP_STATE)
        assert "Freedom station" in prose
        assert "assumed lost" in prose

    def test_elapsed_prose_moments(self):
        """Elapsed 00:00:00 should render as 'moments'."""
        prose = render_ship_state_for_argon(DEFAULT_SHIP_STATE)
        assert "moments since the impact" in prose

    def test_elapsed_prose_hours(self):
        state = {**DEFAULT_SHIP_STATE}
        state = dict(DEFAULT_SHIP_STATE)
        state["mission"] = {
            **DEFAULT_SHIP_STATE["mission"],
            "elapsed_since_impact": "02:15:00",
        }
        prose = render_ship_state_for_argon(state)
        assert "2 hours and 15 minutes" in prose

    def test_shadow_side(self):
        state = dict(DEFAULT_SHIP_STATE)
        state["orbit"] = {**DEFAULT_SHIP_STATE["orbit"], "lit_side": False}
        prose = render_ship_state_for_argon(state)
        assert "Shadow side" in prose

    def test_all_pumps_stopped(self):
        state = dict(DEFAULT_SHIP_STATE)
        state["reactor"] = {
            **DEFAULT_SHIP_STATE["reactor"],
            "coolant_pumps": {"running": 0, "total": 3},
        }
        prose = render_ship_state_for_argon(state)
        assert "All coolant pumps stopped" in prose
