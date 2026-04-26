"""Tests for mirs_end_bridge.prompts."""

import pytest

from mirs_end_bridge.prompts import compose_prompt
from mirs_end_bridge.types import GameState
from mirs_end_bridge.voice_kit import clear_cache


@pytest.fixture(autouse=True)
def _clear_voice_cache():
    clear_cache()
    yield
    clear_cache()


def _make_state(**overrides) -> GameState:
    base = GameState(
        currentRoom="Command Module",
        inventory=["wrench"],
        truthStates={"power-is-restored": False},
        resources={"o2": 90, "morale": 75, "dose": None},
        score=10,
        turn=3,
        recentTranscript="",
        shipState={},
    )
    base.update(overrides)  # type: ignore[arg-type]
    return base


class TestComposePrompt:
    def test_station_ai_system_includes_persona(self):
        prompt = compose_prompt("station-ai", _make_state(), player_utterance="Hello?")
        assert "Argon-87" in prompt["system"]

    def test_narrator_system_includes_writing_style(self):
        prompt = compose_prompt("narrator", _make_state())
        assert "em-dash" in prompt["system"].lower()

    def test_game_state_block_in_system(self):
        prompt = compose_prompt("station-ai", _make_state(), player_utterance="Hi")
        assert "Command Module" in prompt["system"]
        assert "Turn: 3" in prompt["system"]
        assert "Score: 10" in prompt["system"]

    def test_voice_samples_included(self):
        prompt = compose_prompt("narrator", _make_state())
        assert "Darkling Beetles" in prompt["system"]
        assert "The Man, Ava" in prompt["system"]

    def test_player_utterance_in_messages(self):
        prompt = compose_prompt(
            "station-ai", _make_state(), player_utterance="Can you hear me?"
        )
        messages = prompt["messages"]
        last_msg = messages[-1]
        assert last_msg["role"] == "user"
        assert "Can you hear me?" in last_msg["content"]

    def test_scene_label_in_messages(self):
        prompt = compose_prompt("narrator", _make_state(), scene_label="Act 1")
        last_msg = prompt["messages"][-1]
        assert "Scene: Act 1" in last_msg["content"]

    def test_transcript_creates_context_turns(self):
        state = _make_state(recentTranscript="You enter the reactor bay.")
        prompt = compose_prompt("station-ai", state, player_utterance="Hi")
        # Should have transcript context + assistant ack + user message
        assert len(prompt["messages"]) == 3
        assert "transcript" in prompt["messages"][0]["content"].lower()

    def test_extra_context_included(self):
        prompt = compose_prompt(
            "director", _make_state(), extra_context="Player is low on morale."
        )
        assert "Player is low on morale" in prompt["system"]

    def test_empty_inventory_shows_empty(self):
        state = _make_state(inventory=[])
        prompt = compose_prompt("narrator", state)
        assert "Inventory: empty" in prompt["system"]

    def test_ship_state_prose_in_system(self):
        ship = {
            "mission": {
                "turn": 1,
                "clock_utc": "1987-10-24T03:02:34Z",
                "elapsed_since_impact": "00:01:07",
            },
            "orbit": {
                "altitude_km": 352,
                "region": "over Russia (Moscow corridor)",
                "lit_side": True,
                "time_to_terminator_s": 1173,
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
                "isolated_bus": {"state": "online", "feeds": ["status_console"]},
                "armored_bus": "offline",
            },
            "comms": {"array": "patched", "signal_floor": "static", "contacts": {}},
            "hull": {"central_node": "sealed", "other_modules": "nominal"},
            "armament": {
                "bay_hatch": "locked",
                "fire_control": "offline",
                "shells_remaining": 3,
            },
            "propulsion": {
                "fuel_pct": 78,
                "engine": "cold",
                "delta_v_available_mps": 340,
            },
            "docked": {"soyuz": "nominal", "progress": "nominal"},
            "crew": {"known_alive": ["self"], "known_dead": [], "unknown": []},
        }
        state = _make_state(shipState=ship)
        prompt = compose_prompt("station-ai", state, player_utterance="Status?")
        assert "Ship status (prose)" in prompt["system"]
        assert "Reactor: idled" in prompt["system"]
