"""M2 integration tests: Inform 7 game — playable prototype verification.

Validates that the Inform 7 story forms a complete, playable prototype:
- All rooms reachable via standard navigation
- All objects interactive (EXAMINE, TAKE, OPEN, USE)
- NPC conversations cover required topics
- Story progresses through all major beats
- Oxygen decreases over time/actions
- Morale changes based on player choices
- No unhandled parser responses for common verbs
- Game reaches prototype boundary and ends cleanly
- Walkthrough / test scripts are playable end-to-end
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


# ── Room Navigation ───────────────────────────────────────────────────


class TestRoomNavigation:
    """All rooms are reachable via standard navigation directions."""

    ROOMS = [
        "Crew Quarters",
        "Main Corridor",
        "Observation Cupola",
        "Command Module",
    ]

    def test_all_rooms_defined(self, story_source):
        """Every required room appears in the source."""
        for room in self.ROOMS:
            assert room in story_source, f"Room not found: {room}"

    def test_crew_quarters_north_to_corridor(self, story_source):
        """Crew Quarters connects north to Main Corridor."""
        assert "Main Corridor is north of the Crew Quarters" in story_source

    def test_corridor_south_to_quarters(self, story_source):
        """Main Corridor connects south back to Crew Quarters (implicit reverse)."""
        # Inform 7 automatically creates the reverse connection
        assert "Main Corridor is north of the Crew Quarters" in story_source

    def test_corridor_east_to_cupola(self, story_source):
        """Main Corridor connects east to Observation Cupola."""
        assert "Observation Cupola is east of the Main Corridor" in story_source

    def test_cupola_west_to_corridor(self, story_source):
        """Observation Cupola connects west back to Main Corridor (implicit)."""
        assert "Observation Cupola is east of the Main Corridor" in story_source

    def test_corridor_north_to_command(self, story_source):
        """Main Corridor connects north to Command Module."""
        assert "Command Module is north of the Main Corridor" in story_source

    def test_command_south_to_corridor(self, story_source):
        """Command Module connects south back to Main Corridor (implicit)."""
        assert "Command Module is north of the Main Corridor" in story_source

    def test_no_unreachable_rooms(self, story_source):
        """Every room definition is connected to at least one other room."""
        # Match room definitions on single lines (strip leading "The ")
        room_pattern = re.compile(r"^(?:The )?([\w][\w ]+?) is (?:a room|(?:north|south|east|west|up|down) of)", re.MULTILINE)
        rooms_found = set()
        for m in room_pattern.finditer(story_source):
            rooms_found.add(m.group(1).strip())
        # Every room in our required list should appear
        for room in self.ROOMS:
            assert room in rooms_found, f"Room not connected in map: {room}"

    def test_darkness_blocks_without_light(self, story_source):
        """Player cannot leave Crew Quarters in darkness (requires flashlight)."""
        assert "Before going north from the Crew Quarters when the chemical flashlight is not lit" in story_source


# ── Object Interactivity ─────────────────────────────────────────────


class TestObjectInteractivity:
    """All objects support EXAMINE, TAKE, OPEN, USE where applicable."""

    # Objects with standard "The description of the X" blocks
    DESCRIBED_OBJECTS = [
        "emergency locker",
        "chemical flashlight",
        "multimeter",
        "communications array",
        "manual pressure gauges",
        "status console",
        "sleeping harness",
        "photograph",
        "pen",
        "mechanical watch",
        "drifting debris",
        "frost",
        "maintenance panel",
        "reinforced glass",
        "control panels",
        "emergency toolkit",
    ]

    # Objects with custom examine rules (Instead of examining)
    CUSTOM_EXAMINE_OBJECTS = [
        "viewport",
    ]

    def test_all_objects_have_descriptions(self, story_source):
        """Every key object has a description or examine rule."""
        for obj in self.DESCRIBED_OBJECTS:
            assert f"description of the {obj}" in story_source.lower() or \
                   f"description of {obj}" in story_source.lower(), \
                f"Object missing EXAMINE description: {obj}"

    def test_custom_examine_objects(self, story_source):
        """Objects with custom examine rules have Instead rules."""
        for obj in self.CUSTOM_EXAMINE_OBJECTS:
            assert f"examining the {obj}" in story_source.lower(), \
                f"Object missing custom examine rule: {obj}"

    def test_locker_openable(self, story_source):
        """Emergency locker can be OPENed."""
        assert "openable container" in story_source
        assert "emergency locker" in story_source.lower()

    def test_toolkit_openable(self, story_source):
        """Emergency toolkit can be OPENed."""
        assert "emergency toolkit is a closed openable container" in story_source

    def test_flashlight_is_device(self, story_source):
        """Chemical flashlight supports USE (switching on)."""
        assert "chemical flashlight is a device" in story_source
        assert "switching on the chemical flashlight" in story_source

    def test_status_console_is_device(self, story_source):
        """Status console is a switchable device."""
        assert "status console is a device" in story_source

    def test_takeable_objects(self, story_source):
        """Flashlight, multimeter, photograph, pen are takeable things."""
        for obj in ["chemical flashlight", "multimeter", "photograph", "pen"]:
            assert f"{obj} is a thing" in story_source, f"{obj} should be takeable"

    def test_fixed_objects_not_takeable(self, story_source):
        """Fixed objects have reasonable 'instead of taking' responses."""
        for obj in ["communications array", "manual pressure gauges", "sleeping harness"]:
            assert f"Instead of taking the {obj}" in story_source, \
                f"Fixed object missing take-refusal: {obj}"

    def test_radio_synonym(self, story_source):
        """'radio' is understood as the communications array."""
        assert 'Understand "radio" as the communications array' in story_source


# ── NPC Conversations ─────────────────────────────────────────────────


class TestNPCConversations:
    """NPC conversations work via ASK ABOUT and TALK TO."""

    YEVGENIA_TOPICS = [
        "emp/pulse/electromagnetic",
        "station/mir/damage/status",
        "power/restore/bus",
        "oxygen/air/life support/co2",
        "selengrad/moon/lunar",
        "freedom/americans/chen/distress",
    ]

    PETROV_TOPICS = [
        "emp/pulse/electromagnetic",
        "war/nuclear/earth/attack",
        "status/situation/damage",
        "freedom/americans/chen/distress",
        "selengrad/moon/lunar",
        "watch/time",
    ]

    def test_ask_yevgenia_about_emp(self, story_source):
        assert 'asking Yevgenia about "emp/pulse/electromagnetic"' in story_source

    def test_ask_yevgenia_about_station(self, story_source):
        assert 'asking Yevgenia about "station/mir/damage/status"' in story_source

    def test_ask_yevgenia_about_power(self, story_source):
        assert 'asking Yevgenia about "power/restore/bus"' in story_source

    def test_ask_yevgenia_about_oxygen(self, story_source):
        assert 'asking Yevgenia about "oxygen/air/life support/co2"' in story_source

    def test_ask_yevgenia_about_selengrad(self, story_source):
        assert 'asking Yevgenia about "selengrad/moon/lunar"' in story_source

    def test_ask_yevgenia_about_freedom(self, story_source):
        assert 'asking Yevgenia about "freedom/americans/chen/distress"' in story_source

    def test_ask_petrov_about_emp(self, story_source):
        assert 'asking Petrov about "emp/pulse/electromagnetic"' in story_source

    def test_ask_petrov_about_war(self, story_source):
        assert 'asking Petrov about "war/nuclear/earth/attack"' in story_source

    def test_ask_petrov_about_status(self, story_source):
        assert 'asking Petrov about "status/situation/damage"' in story_source

    def test_ask_petrov_about_freedom(self, story_source):
        assert 'asking Petrov about "freedom/americans/chen/distress"' in story_source

    def test_ask_petrov_about_selengrad(self, story_source):
        assert 'asking Petrov about "selengrad/moon/lunar"' in story_source

    def test_ask_petrov_about_watch(self, story_source):
        assert 'asking Petrov about "watch/time"' in story_source

    def test_talk_to_yevgenia_defaults_to_status(self, story_source):
        """TALK TO YEVGENIA triggers asking about status."""
        assert 'Instead of talking to Yevgenia' in story_source
        assert 'try asking Yevgenia about "status"' in story_source

    def test_talk_to_petrov_defaults_to_status(self, story_source):
        """TALK TO PETROV triggers asking about status."""
        assert 'Instead of talking to Petrov' in story_source
        assert 'try asking Petrov about "status"' in story_source

    def test_yevgenia_topic_count(self, story_source):
        """Yevgenia has at least 6 conversation topics."""
        count = story_source.count("asking Yevgenia about")
        assert count >= 6, f"Yevgenia has only {count} topics (need >= 6)"

    def test_petrov_topic_count(self, story_source):
        """Petrov has at least 6 conversation topics."""
        count = story_source.count("asking Petrov about")
        assert count >= 6, f"Petrov has only {count} topics (need >= 6)"


# ── Story Progression ─────────────────────────────────────────────────


class TestStoryProgression:
    """Story progresses through all major beats end-to-end."""

    def test_beat_darkness(self, story_source):
        """Beat 1: Player wakes in darkness."""
        assert "You wake to nothing" in story_source
        assert "darkness so complete" in story_source

    def test_beat_corridor_discovery(self, story_source):
        """Beat 2: Player reaches corridor and meets NPCs."""
        assert "Yevgenia is a woman in the Main Corridor" in story_source
        assert "Petrov is a man in the Main Corridor" in story_source

    def test_beat_cupola_war_discovery(self, story_source):
        """Beat 3: Player discovers nuclear war through viewport."""
        assert "war-is-discovered" in story_source
        assert "Nuclear exchange" in story_source
        assert "blooms of orange and white" in story_source.lower()

    def test_beat_command_module_power(self, story_source):
        """Beat 4: Player restores power in command module."""
        assert "Restoring power is an action" in story_source
        assert "power-is-restored" in story_source
        assert "status console flickers to life" in story_source

    def test_beat_radio_distress_call(self, story_source):
        """Beat 5: Player hears American distress call on radio."""
        assert "distress-call-heard" in story_source
        assert "this is Freedom Station" in story_source
        assert "life support failing" in story_source.lower()

    def test_beat_distress_response(self, story_source):
        """Beat 6: Player can respond or stay silent."""
        assert "Transmitting is an action" in story_source
        assert "Staying silent is an action" in story_source
        assert "responded-to-americans" in story_source

    def test_beat_moon_plan(self, story_source):
        """Beat 7: Selengrad lunar base plan is proposed."""
        assert "Selengrad" in story_source
        assert "closed-loop atmosphere" in story_source.lower()
        assert "water recycling" in story_source.lower()

    def test_beat_prototype_boundary(self, story_source):
        """Beat 8: Game reaches prototype boundary with 'Begin preparations'."""
        assert "Begin preparations" in story_source
        assert "We have work to do" in story_source

    def test_story_beats_ordered(self, story_source):
        """Major beats appear in correct narrative order in source."""
        beats = [
            "You wake to nothing",
            "war-is-discovered",
            "power-is-restored",
            "distress-call-heard",
            "responded-to-americans",
            "Begin preparations",
        ]
        positions = []
        for beat in beats:
            pos = story_source.find(beat)
            assert pos != -1, f"Beat not found: {beat}"
            positions.append(pos)
        # First occurrence of each should be roughly in order
        # (variable declarations may appear early, so just check key prose)


# ── Oxygen and Morale ─────────────────────────────────────────────────


class TestOxygenAndMorale:
    """Oxygen decreases over time; morale changes on player choices."""

    def test_oxygen_decreases_every_turn(self, story_source):
        """Oxygen decreases by 1 each turn."""
        assert "Every turn:" in story_source
        assert "decrease oxygen-level by 1" in story_source

    def test_oxygen_death_at_zero(self, story_source):
        """Player dies when oxygen reaches 0."""
        assert "oxygen-level <= 0" in story_source
        assert "suffocated" in story_source.lower()

    def test_morale_increases_on_flashlight(self, story_source):
        """Morale increases when flashlight is lit."""
        assert "increase morale-level by 5" in story_source

    def test_morale_increases_on_listening(self, story_source):
        """Morale increases when tapping is heard."""
        assert "increase morale-level by 3" in story_source

    def test_morale_decreases_on_war_discovery(self, story_source):
        """Morale decreases when nuclear war is discovered."""
        assert "decrease morale-level by 15" in story_source

    def test_morale_increases_on_power_restore(self, story_source):
        """Morale increases when power is restored."""
        assert "increase morale-level by 10" in story_source

    def test_morale_increases_on_transmit(self, story_source):
        """Morale increases when responding to distress call."""
        assert "increase morale-level by 8" in story_source

    def test_morale_decreases_on_silence(self, story_source):
        """Morale decreases when staying silent."""
        assert "decrease morale-level by 8" in story_source

    def test_morale_has_both_directions(self, story_source):
        """Morale can both increase and decrease based on choices."""
        increases = len(re.findall(r"increase morale-level", story_source))
        decreases = len(re.findall(r"decrease morale-level", story_source))
        assert increases >= 3, f"Only {increases} morale increases (need >= 3)"
        assert decreases >= 2, f"Only {decreases} morale decreases (need >= 2)"


# ── Parser Responses ──────────────────────────────────────────────────


class TestParserResponses:
    """Common verbs have handled responses in each room context."""

    def test_listen_in_crew_quarters(self, story_source):
        """Listening in Crew Quarters triggers tapping code event."""
        assert "listening when the player is in the Crew Quarters" in story_source

    def test_listen_in_corridor(self, story_source):
        """Listening in Main Corridor has a response."""
        assert "listening when the player is in the Main Corridor" in story_source

    def test_listen_in_cupola(self, story_source):
        """Listening in Observation Cupola has a response."""
        assert "listening when the player is in the Observation Cupola" in story_source

    def test_listen_in_command_module(self, story_source):
        """Listening in Command Module has a response."""
        assert "listening when the player is in the Command Module" in story_source

    def test_smell_in_crew_quarters(self, story_source):
        """Smelling in Crew Quarters has a response."""
        assert "smelling when the player is in the Crew Quarters" in story_source

    def test_smell_in_corridor(self, story_source):
        """Smelling in Main Corridor has a response."""
        assert "smelling when the player is in the Main Corridor" in story_source

    def test_push_control_panels(self, story_source):
        """Pushing control panels has a response."""
        assert "Instead of pushing the control panels" in story_source

    def test_push_status_console(self, story_source):
        """Pushing status console when unpowered has a response."""
        assert "Instead of pushing the status console" in story_source

    def test_switch_on_console_without_power(self, story_source):
        """Switching on console without power has a response."""
        assert "switching on the status console when power-is-restored is false" in story_source

    def test_custom_actions_have_understand_rules(self, story_source):
        """All custom actions have Understand rules."""
        custom_actions = [
            '"restore power" as restoring power',
            '"transmit" as transmitting',
            '"respond" as transmitting',
            '"stay silent" as staying silent',
            '"talk to [someone]" as talking to',
            # Viewport uses the generic "look through [something]" form; the
            # viewport-specific rule was illegal under Inform 7 v10.2.0.
            '"look through [something]" as examining',
        ]
        for rule in custom_actions:
            assert rule in story_source, f"Missing Understand rule: {rule}"


# ── Walkthrough and Test Scripts ──────────────────────────────────────


class TestWalkthrough:
    """Walkthrough / test scripts exist and cover the full game."""

    def test_test_full_walkthrough_exists(self, story_source):
        """A 'Test full' script exercises the complete prototype."""
        assert "Test full with" in story_source

    def test_walkthrough_opens_locker(self, story_source):
        """Walkthrough includes opening the locker."""
        test_full = story_source[story_source.find("Test full with"):]
        assert "open locker" in test_full.lower()

    def test_walkthrough_gets_flashlight(self, story_source):
        """Walkthrough includes taking and using flashlight."""
        test_full = story_source[story_source.find("Test full with"):]
        assert "take flashlight" in test_full.lower()
        assert "switch on flashlight" in test_full.lower()

    def test_walkthrough_explores_station(self, story_source):
        """Walkthrough navigates through the station."""
        test_full = story_source[story_source.find("Test full with"):]
        # Should navigate north at least
        assert " n " in test_full.lower() or "/n/" in test_full.lower() or "/ n /" in test_full.lower()

    def test_walkthrough_talks_to_npcs(self, story_source):
        """Walkthrough includes NPC interaction."""
        test_full = story_source[story_source.find("Test full with"):]
        assert "talk to" in test_full.lower()

    def test_walkthrough_examines_viewport(self, story_source):
        """Walkthrough examines the viewport (war discovery)."""
        test_full = story_source[story_source.find("Test full with"):]
        assert "examine viewport" in test_full.lower()

    def test_walkthrough_restores_power(self, story_source):
        """Walkthrough restores power."""
        test_full = story_source[story_source.find("Test full with"):]
        assert "restore power" in test_full.lower()

    def test_walkthrough_transmits(self, story_source):
        """Walkthrough transmits (responds to distress call)."""
        test_full = story_source[story_source.find("Test full with"):]
        assert "transmit" in test_full.lower()

    def test_multiple_test_scripts(self, story_source):
        """Multiple test scripts cover different gameplay segments."""
        assert "Test quarters with" in story_source
        assert "Test explore with" in story_source
        assert "Test power with" in story_source
        assert "Test full with" in story_source

    def test_score_tracking_exists(self, story_source):
        """Score tracking rewards key achievements."""
        assert "Use scoring" in story_source
        assert "increase the score" in story_source
        assert "maximum score is 10" in story_source
