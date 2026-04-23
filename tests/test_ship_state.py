"""
Unit tests for lib/ship-state.js

Runs the JS module via Node.js subprocess and validates behavior through
a thin JSON bridge. Each test calls a small inline ES module script that
imports from lib/ship-state.js and prints JSON results.
"""

import json
import os
import subprocess
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(REPO_ROOT, "lib", "ship-state.js")


def run_js(script):
    """Run an inline ES module script that can import from lib/ship-state.js."""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"JS error:\n{result.stderr}")
    return result.stdout.strip()


def run_js_json(script):
    """Run JS and parse stdout as JSON."""
    return json.loads(run_js(script))


# ── Helpers ──────────────────────────────────────────────────────────────────

IMPORT_LINE = 'import { initShipState, tickShipState, applyDelta, getShipState, renderShipStateForArgon, _internals } from "./lib/ship-state.js";'


# ── initShipState tests ─────────────────────────────────────────────────────


class TestInitShipState:
    def test_returns_default_state(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            const s = initShipState();
            console.log(JSON.stringify(s));
        """)
        assert state["mission"]["turn"] == 0
        assert state["reactor"]["state"] == "idled"
        assert state["power"]["main_bus"] == "offline"
        assert state["crew"]["known_alive"] == ["self"]

    def test_accepts_overrides(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            const s = initShipState({{ reactor: {{ state: "running" }} }});
            console.log(JSON.stringify(s));
        """)
        assert state["reactor"]["state"] == "running"
        # Other reactor fields preserved via deep merge
        assert state["reactor"]["coolant_pumps"]["running"] == 2

    def test_default_data_shape(self):
        """Verify all top-level keys exist in the canonical shape."""
        state = run_js_json(f"""
            {IMPORT_LINE}
            const s = initShipState();
            console.log(JSON.stringify(s));
        """)
        expected_keys = [
            "mission", "orbit", "reactor", "life_support", "power",
            "comms", "hull", "armament", "propulsion", "docked", "crew",
        ]
        for key in expected_keys:
            assert key in state, f"Missing top-level key: {key}"


# ── tickShipState tests ─────────────────────────────────────────────────────


class TestTickShipState:
    def test_advances_turn(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            tickShipState();
            const s = getShipState();
            console.log(JSON.stringify(s));
        """)
        assert state["mission"]["turn"] == 1

    def test_orbit_cycles_12_steps(self):
        """Orbit should cycle back to the start after 12 turns."""
        result = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            const regions = [];
            for (let i = 0; i < 24; i++) {{
                tickShipState();
                regions.push(getShipState().orbit.region);
            }}
            console.log(JSON.stringify(regions));
        """)
        # Turns 1-12 should equal turns 13-24
        assert result[:12] == result[12:]

    def test_orbit_all_12_entries(self):
        """All 12 orbit table entries should appear in one cycle."""
        result = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            const regions = [];
            for (let i = 0; i < 12; i++) {{
                tickShipState();
                regions.push(getShipState().orbit.region);
            }}
            console.log(JSON.stringify(regions));
        """)
        assert len(set(result)) == 12

    def test_temperature_falls_without_power(self):
        """Temperature should drift downward when main bus is offline."""
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            // Tick several times with power off
            for (let i = 0; i < 5; i++) tickShipState();
            console.log(JSON.stringify(getShipState()));
        """)
        # Should have drifted below "nominal"
        assert state["life_support"]["temperature"] in ["cool", "cold", "freezing"]

    def test_temperature_stable_with_power(self):
        """Temperature should not fall when main power is online."""
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState({{ power: {{ main_bus: "online" }} }});
            const initial = getShipState().life_support.temperature;
            for (let i = 0; i < 5; i++) tickShipState();
            const s = getShipState();
            console.log(JSON.stringify({{ initial, final: s.life_support.temperature }}));
        """)
        assert state["initial"] == state["final"]

    def test_co2_rises_with_passive_lioh(self):
        """CO2 should rise when LiOH is passive."""
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState({{ life_support: {{ co2_trend: "stable", lioh_mode: "passive" }} }});
            tickShipState();
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["life_support"]["co2_trend"] == "rising slow"

    def test_co2_falls_with_active_lioh(self):
        """CO2 should decrease when LiOH is active."""
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState({{ life_support: {{ co2_trend: "rising slow", lioh_mode: "active" }} }});
            tickShipState();
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["life_support"]["co2_trend"] == "stable"

    def test_mission_clock_advances(self):
        """Mission clock should advance with each tick."""
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            tickShipState();
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["mission"]["elapsed_since_impact"] != "00:00:00"
        assert state["mission"]["clock_utc"] != "1987-10-24T03:01:27Z"

    def test_throws_without_init(self):
        """tickShipState should throw if state is not initialized."""
        result = run_js(f"""
            import {{ tickShipState }} from "./lib/ship-state.js";
            try {{
                tickShipState();
                console.log("NO_ERROR");
            }} catch (e) {{
                console.log("ERROR:" + e.message);
            }}
        """)
        assert result.startswith("ERROR:")


# ── applyDelta tests ────────────────────────────────────────────────────────


class TestApplyDelta:
    def test_cannon_fired_decrements_shells(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("cannon_fired", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["armament"]["shells_remaining"] == 2

    def test_cannon_fired_multiple(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("cannon_fired", {{}});
            applyDelta("cannon_fired", {{}});
            applyDelta("cannon_fired", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["armament"]["shells_remaining"] == 0

    def test_cannon_fired_no_negative(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            for (let i = 0; i < 5; i++) applyDelta("cannon_fired", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["armament"]["shells_remaining"] == 0

    def test_dosimeter_taken(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("dosimeter_taken", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert "dosimeter" in state["crew"]["equipped"]

    def test_dosimeter_taken_idempotent(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("dosimeter_taken", {{}});
            applyDelta("dosimeter_taken", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["crew"]["equipped"].count("dosimeter") == 1

    def test_power_restored_truth_state(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("power-is-restored", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["power"]["main_bus"] == "online"
        assert state["power"]["armored_bus"] == "online"
        assert state["reactor"]["state"] == "running"
        assert state["life_support"]["o2_generator"] == "online"
        assert state["life_support"]["lioh_mode"] == "active"

    def test_armament_bay_unlocked(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("armament-bay-unlocked", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["armament"]["bay_hatch"] == "unlocked"
        assert state["armament"]["fire_control"] == "standby"

    def test_reactor_scrammed(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("reactor-scrammed", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["reactor"]["state"] == "scrammed"
        assert state["reactor"]["coolant_pumps"]["running"] == 0
        assert state["reactor"]["core_temp"] == "hot"

    def test_comms_restored(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("comms-restored", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["comms"]["signal_floor"] == "weak"
        assert state["comms"]["contacts"]["freedom_station"]["live_channel"] is True

    def test_coolant_pump_failed(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("coolant_pump_failed", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["reactor"]["coolant_pumps"]["running"] == 1

    def test_coolant_pump_restarted(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("coolant_pump_failed", {{}});
            applyDelta("coolant_pump_restarted", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["reactor"]["coolant_pumps"]["running"] == 2

    def test_crew_found_alive(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState({{ crew: {{ unknown: ["Ivanov"] }} }});
            applyDelta("crew_found_alive", {{ name: "Ivanov" }});
            console.log(JSON.stringify(getShipState()));
        """)
        assert "Ivanov" in state["crew"]["known_alive"]
        assert "Ivanov" not in state["crew"]["unknown"]

    def test_crew_found_dead(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState({{ crew: {{ unknown: ["Ivanov"] }} }});
            applyDelta("crew_found_dead", {{ name: "Ivanov" }});
            console.log(JSON.stringify(getShipState()));
        """)
        assert "Ivanov" in state["crew"]["known_dead"]
        assert "Ivanov" not in state["crew"]["unknown"]

    def test_fuel_consumed(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("fuel_consumed", {{ amount: 10 }});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["propulsion"]["fuel_pct"] == 68

    def test_fire_control_activated(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("fire_control_activated", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["armament"]["fire_control"] == "online"

    def test_soyuz_detached(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("soyuz-detached", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["docked"]["soyuz"] == "detached"

    def test_engine_fired(self):
        state = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("engine-fired", {{}});
            console.log(JSON.stringify(getShipState()));
        """)
        assert state["propulsion"]["engine"] == "firing"

    def test_invalid_event_rejected(self):
        result = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            try {{
                applyDelta("nonexistent_event", {{}});
                console.log("NO_ERROR");
            }} catch (e) {{
                console.log("ERROR:" + e.message);
            }}
        """)
        assert result.startswith("ERROR:")
        assert "nonexistent_event" in result


# ── getShipState tests ───────────────────────────────────────────────────────


class TestGetShipState:
    def test_returns_deep_copy(self):
        """Mutations to the returned snapshot should not affect internal state."""
        result = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            const snap = getShipState();
            snap.reactor.state = "MUTATED";
            const fresh = getShipState();
            console.log(JSON.stringify({{ mutated: snap.reactor.state, fresh: fresh.reactor.state }}));
        """)
        assert result["mutated"] == "MUTATED"
        assert result["fresh"] == "idled"


# ── renderShipStateForArgon tests ────────────────────────────────────────────


class TestRenderShipStateForArgon:
    def test_no_em_dashes(self):
        """Voice output must never contain em-dashes."""
        output = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        assert "\u2014" not in output, "Found em-dash in voice output"
        assert "\u2013" not in output, "Found en-dash in voice output"

    def test_contains_time_block(self):
        output = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        assert "[Time onboard]" in output
        assert "Mission clock" in output
        assert "since the impact" in output

    def test_contains_orbit_block(self):
        output = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        assert "[Where we are]" in output
        assert "kilometres up" in output

    def test_contains_systems_block(self):
        output = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        assert "[My systems]" in output
        assert "Reactor:" in output
        assert "Life support:" in output
        assert "Main power:" in output

    def test_contains_all_systems(self):
        output = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        for system in ["Reactor", "Life support", "Main power", "Comms", "Hull", "Armament", "Propulsion", "Docked", "Crew"]:
            assert system in output, f"Missing system in voice output: {system}"

    def test_paragraph_count(self):
        """Voice output should be concise (under 30 lines)."""
        output = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        lines = [l for l in output.split("\n") if l.strip()]
        assert len(lines) < 30, f"Voice output too long: {len(lines)} lines"

    def test_prose_after_power_restored(self):
        """Voice should reflect power-restored state."""
        output = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            applyDelta("power-is-restored", {{}});
            console.log(renderShipStateForArgon());
        """)
        assert "online" in output.lower()

    def test_prose_updates_after_tick(self):
        """Voice should reflect orbit changes after ticking."""
        outputs = run_js_json(f"""
            {IMPORT_LINE}
            initShipState();
            const before = renderShipStateForArgon();
            for (let i = 0; i < 3; i++) tickShipState();
            const after = renderShipStateForArgon();
            console.log(JSON.stringify({{ before, after }}));
        """)
        # Region should have changed after 3 ticks
        assert outputs["before"] != outputs["after"]
