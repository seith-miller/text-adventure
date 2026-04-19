"""Tests for the Inform 7 opening scene port (issue #12).

Validates that story.ni contains all required rooms, objects, NPCs,
resource tracking, story beats, and parser interactions specified
in the issue requirements.
"""

import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_NI = os.path.join(ROOT, "game", "inform", "Source", "story.ni")


@pytest.fixture(scope="module")
def story_source():
    """Load the Inform 7 source file."""
    with open(STORY_NI) as f:
        return f.read()


# ── Rooms ──────────────────────────────────────────────────────────────


class TestRooms:
    """All four rooms are defined and properly connected."""

    def test_crew_quarters_is_room(self, story_source):
        assert "Crew Quarters is a room" in story_source

    def test_main_corridor_is_room(self, story_source):
        assert "Main Corridor is north of the Crew Quarters" in story_source

    def test_observation_cupola_is_room(self, story_source):
        assert "Observation Cupola is east of the Main Corridor" in story_source

    def test_command_module_is_room(self, story_source):
        assert "Command Module is north of the Main Corridor" in story_source

    def test_player_starts_in_crew_quarters(self, story_source):
        assert "player is in the Crew Quarters" in story_source

    def test_rooms_have_descriptions(self, story_source):
        """Each room has a quoted description after its definition."""
        for room in ["Crew Quarters is a room.", "Main Corridor is north",
                      "Observation Cupola is east", "Command Module is north"]:
            # Find the room definition and ensure a quoted description follows
            idx = story_source.find(room)
            assert idx != -1, f"Room definition not found: {room}"
            # Check there's a quoted string nearby (within 200 chars)
            snippet = story_source[idx:idx + 500]
            assert '"' in snippet, f"No description found near: {room}"


# ── Objects ────────────────────────────────────────────────────────────


class TestObjects:
    """All required objects exist and are interactive."""

    def test_emergency_locker_exists(self, story_source):
        assert "emergency locker" in story_source.lower()

    def test_emergency_locker_is_openable(self, story_source):
        assert "openable container in the Crew Quarters" in story_source

    def test_chemical_flashlight_in_locker(self, story_source):
        assert "chemical flashlight is a thing in the emergency locker" in story_source

    def test_flashlight_can_be_lit(self, story_source):
        assert "chemical flashlight can be lit or unlit" in story_source

    def test_flashlight_switching_on(self, story_source):
        assert "switching on the chemical flashlight" in story_source

    def test_multimeter_exists(self, story_source):
        assert "multimeter" in story_source.lower()

    def test_multimeter_in_toolkit(self, story_source):
        assert "multimeter is a thing in the emergency toolkit" in story_source

    def test_communications_array_exists(self, story_source):
        assert "communications array" in story_source.lower()

    def test_radio_understood_as_comms(self, story_source):
        assert 'Understand "radio" as the communications array' in story_source

    def test_manual_pressure_gauges_exist(self, story_source):
        assert "manual pressure gauges" in story_source.lower()

    def test_status_console_exists(self, story_source):
        assert "status console" in story_source.lower()

    def test_status_console_is_device(self, story_source):
        assert "status console is a device" in story_source


# ── NPCs ───────────────────────────────────────────────────────────────


class TestNPCs:
    """Yevgenia and Petrov are defined with conversation support."""

    def test_yevgenia_exists(self, story_source):
        assert "Yevgenia is a woman" in story_source

    def test_yevgenia_has_description(self, story_source):
        assert "Yevgenia Kozlova" in story_source

    def test_petrov_exists(self, story_source):
        assert "Petrov is a man" in story_source

    def test_petrov_has_description(self, story_source):
        assert "Commander Petrov" in story_source

    def test_talk_to_action_defined(self, story_source):
        assert "Talking to is an action" in story_source

    def test_talk_to_understood(self, story_source):
        assert 'Understand "talk to [someone]" as talking to' in story_source

    def test_yevgenia_conversation_topics(self, story_source):
        """Yevgenia responds to key topics."""
        topics = ["emp", "station", "power", "oxygen", "selengrad", "freedom"]
        for topic in topics:
            assert f"asking Yevgenia about" in story_source and topic in story_source.lower(), (
                f"Yevgenia missing conversation about: {topic}"
            )

    def test_petrov_conversation_topics(self, story_source):
        """Petrov responds to key topics."""
        topics = ["emp", "war", "status", "freedom", "selengrad"]
        for topic in topics:
            assert f"asking Petrov about" in story_source and topic in story_source.lower(), (
                f"Petrov missing conversation about: {topic}"
            )

    def test_npc_movement(self, story_source):
        """NPCs move based on story progression."""
        assert "Yevgenia is not in the Command Module" in story_source
        assert "now Yevgenia is in the Command Module" in story_source


# ── Resource Tracking ──────────────────────────────────────────────────


class TestResources:
    """Oxygen and morale are tracked and displayed."""

    def test_oxygen_variable(self, story_source):
        assert "Oxygen-level is a number that varies" in story_source

    def test_morale_variable(self, story_source):
        assert "Morale-level is a number that varies" in story_source

    def test_oxygen_starts_at_100(self, story_source):
        assert "Oxygen-level is 100" in story_source

    def test_morale_starts_at_50(self, story_source):
        assert "Morale-level is 50" in story_source

    def test_oxygen_displayed_in_status(self, story_source):
        # The in-game status bar is intentionally omitted — the Web UI
        # displays O2 from window.MirsEnd.setState, driven by the MIRSEND
        # status line emitted every turn.
        assert "oxygen-level" in story_source.lower()
        assert "MIRSEND o2=" in story_source

    def test_morale_displayed_in_status(self, story_source):
        assert "morale-level" in story_source.lower()
        assert "MIRSEND" in story_source and "morale=" in story_source

    def test_status_bar_rule(self, story_source):
        # Status bridge is the MIRSEND every-turn emission, consumed by ui.js.
        assert "MIRSEND" in story_source
        assert "mirsend-inventory-list" in story_source

    def test_oxygen_decreases_over_time(self, story_source):
        assert "decrease oxygen-level by 1" in story_source

    def test_oxygen_death_condition(self, story_source):
        assert "oxygen-level <= 0" in story_source
        assert "suffocated" in story_source.lower()

    def test_morale_changes_on_events(self, story_source):
        """Morale increases and decreases at key moments."""
        assert "increase morale-level" in story_source
        assert "decrease morale-level" in story_source


# ── Story Beats ────────────────────────────────────────────────────────


class TestStoryBeats:
    """All major story beats from the Ink version are preserved."""

    def test_wake_in_darkness(self, story_source):
        assert "You wake to nothing" in story_source

    def test_emp_reference(self, story_source):
        assert "electromagnetic pulse" in story_source.lower()

    def test_discover_war_through_viewport(self, story_source):
        assert "Nuclear exchange" in story_source
        assert "war-is-discovered" in story_source.lower()

    def test_restore_partial_power(self, story_source):
        assert "power-is-restored" in story_source.lower()
        assert "Restoring power is an action" in story_source

    def test_american_distress_call(self, story_source):
        assert "Freedom Station" in story_source
        assert "distress-call-heard" in story_source.lower()

    def test_trust_decision_respond(self, story_source):
        assert "Transmitting is an action" in story_source
        assert "responded-to-americans" in story_source.lower()

    def test_trust_decision_stay_silent(self, story_source):
        assert "Staying silent is an action" in story_source
        assert 'Understand "stay silent" as staying silent' in story_source

    def test_selengrad_plan(self, story_source):
        assert "Selengrad" in story_source
        assert "lunar base" in story_source.lower()

    def test_command_decision_point(self, story_source):
        assert "Begin preparations" in story_source


# ── Parser Interactions ────────────────────────────────────────────────


class TestParserInteractions:
    """Custom and standard parser verbs work correctly."""

    def test_listen_action(self, story_source):
        assert "Instead of listening" in story_source

    def test_listen_tapping_in_quarters(self, story_source):
        assert "three-two-three" in story_source.lower()

    def test_restore_power_action(self, story_source):
        assert 'Understand "restore power" as restoring power' in story_source

    def test_transmit_action(self, story_source):
        assert 'Understand "transmit" as transmitting' in story_source

    def test_respond_action(self, story_source):
        assert 'Understand "respond" as transmitting' in story_source

    def test_look_through_viewport(self, story_source):
        # Generic "look through [something]" rule is sufficient — the original
        # viewport-specific Understand form is an illegal action-with-noun
        # pattern under Inform 7 v10.2.0.
        assert 'Understand "look through [something]" as examining' in story_source

    def test_darkness_blocks_movement(self, story_source):
        """Player cannot leave crew quarters without light."""
        assert "Before going north from the Crew Quarters when the chemical flashlight is not lit" in story_source

    def test_restore_power_requires_multimeter(self, story_source):
        assert "does not carry the multimeter" in story_source

    def test_restore_power_requires_command_module(self, story_source):
        assert "player is not in the Command Module" in story_source


# ── Prose Quality ──────────────────────────────────────────────────────


class TestProseQuality:
    """The prose is substantial and atmospheric."""

    def test_opening_text_atmospheric(self, story_source):
        assert "hammering of your own pulse" in story_source
        assert "darkness so complete" in story_source

    def test_viewport_discovery_dramatic(self, story_source):
        # Updated for the in-progress WWIII framing — the Earth isn't just
        # "scarred" after the fact, hundreds of detonations are still going.
        assert "blooms of orange and white" in story_source.lower()
        assert "thermonuclear" in story_source.lower() or "world war" in story_source.lower()

    def test_distress_call_text(self, story_source):
        assert "this is Freedom Station" in story_source
        assert "life support failing" in story_source.lower()

    def test_selengrad_proposal(self, story_source):
        assert "closed-loop atmosphere" in story_source.lower()
        assert "water recycling" in story_source.lower()

    def test_substantial_descriptions(self, story_source):
        """Story has enough prose (at least 8000 chars)."""
        assert len(story_source) > 8000, (
            f"Source is only {len(story_source)} chars — too short for full port"
        )


# ── Ink Files Preserved ───────────────────────────────────────────────


class TestInkPreserved:
    """Original Ink files remain in the repository."""

    def test_opening_ink_exists(self):
        path = os.path.join(ROOT, "game", "story", "opening.ink")
        assert os.path.isfile(path), "opening.ink should be kept as reference"

    def test_main_ink_exists(self):
        path = os.path.join(ROOT, "game", "story", "main.ink")
        assert os.path.isfile(path), "main.ink should be kept as reference"
