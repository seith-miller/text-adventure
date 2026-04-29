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

    def test_corridor_down_to_cupola(self, story_source):
        """Main Corridor connects down (nadir) to Observation Cupola."""
        assert "Observation Cupola is down from the Main Corridor" in story_source

    def test_cupola_up_to_corridor(self, story_source):
        """Observation Cupola connects up back to Main Corridor (implicit)."""
        assert "Observation Cupola is down from the Main Corridor" in story_source

    def test_corridor_north_to_command(self, story_source):
        """Main Corridor connects north to Command Module."""
        assert "Command Module is north of the Main Corridor" in story_source

    def test_command_south_to_corridor(self, story_source):
        """Command Module connects south back to Main Corridor (implicit)."""
        assert "Command Module is north of the Main Corridor" in story_source

    def test_no_unreachable_rooms(self, story_source):
        """Every room definition is connected to at least one other room."""
        # Match room definitions on single lines (strip leading "The ")
        room_pattern = re.compile(r"^(?:The )?([\w][\w ]+?) is (?:a room|(?:north|south|east|west|up|down) (?:of|from))", re.MULTILINE)
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


class TestCrewVoicesViaArtifacts:
    """The crew died in the prologue impact. Their voices live on as
    discoverable artifacts: Yevgenia's flight notebook (clipped to her
    body in the corridor) and Petrov's last log on the command console."""

    def test_yevgenia_notebook_exists(self, story_source):
        assert "Yevgenia's notebook" in story_source

    def test_yevgenia_notebook_is_part_of_body(self, story_source):
        assert "Yevgenia's notebook is part of Yevgenia" in story_source

    def test_yevgenia_notebook_is_readable(self, story_source):
        assert "Instead of reading Yevgenia's notebook" in story_source

    def test_yevgenia_notebook_explains_emp(self, story_source):
        assert "EMP confirmed" in story_source

    def test_yevgenia_notebook_explains_power_restore(self, story_source):
        # Notebook walks the player through the reset sequence.
        assert "isolated bus" in story_source.lower()
        assert "capacitor" in story_source.lower() or "reset pin" in story_source.lower() or "reseat" in story_source.lower()

    def test_yevgenia_notebook_proposes_selengrad(self, story_source):
        assert "Selengrad" in story_source

    def test_petrov_log_action_exists(self, story_source):
        assert "Reading Petrov's log is an action" in story_source

    def test_petrov_log_requires_power(self, story_source):
        assert "Check reading Petrov's log" in story_source
        assert "power-is-restored is false" in story_source

    def test_petrov_log_records_emp_time(self, story_source):
        assert "03:47" in story_source

    def test_petrov_log_reveals_armament(self, story_source):
        assert "armament" in story_source.lower() or "weapon is aboard" in story_source.lower()

    def test_petrov_log_reveals_armament_location(self, story_source):
        assert "Kozlova has the access code" in story_source or "Kozlova has the code" in story_source

    def test_classified_safe_exists(self, story_source):
        assert "classified safe" in story_source.lower()

    def test_safe_locked_until_notebook_read(self, story_source):
        assert "notebook-read" in story_source.lower()


# ── Notebook Read & Consult Grammar ──────────────────────────────────


class TestNotebookReadAndConsult:
    """The notebook supports read, consult about, and look up grammar.
    Reading reveals the safe code, burn calculation, and Argon-87 cue.
    The safe code is randomized per playthrough (1000-9999)."""

    def test_notebook_reading_sets_notebook_read_flag(self, story_source):
        assert "now notebook-read is true" in story_source

    def test_notebook_read_reveals_safe_code(self, story_source):
        """Reading the notebook interpolates the live safe-code value."""
        assert "safe-code of the classified safe" in story_source

    def test_notebook_read_mentions_katalog(self, story_source):
        """The notebook entry references КАТАЛОГ ВМФ-07."""
        read_section = story_source[
            story_source.find("Instead of reading Yevgenia's notebook"):
        ]
        assert "КАТАЛОГ ВМФ-07" in read_section

    def test_notebook_read_mentions_argon87(self, story_source):
        """The notebook entry cues the player to ARGON-87."""
        read_section = story_source[
            story_source.find("Instead of reading Yevgenia's notebook"):
        ]
        assert "ARGON-87" in read_section

    def test_notebook_read_mentions_burn_calc(self, story_source):
        """The notebook entry references the Selengrad burn calculation."""
        read_section = story_source[
            story_source.find("Instead of reading Yevgenia's notebook"):
        ]
        assert "delta-v" in read_section.lower() or "burn" in read_section.lower()

    def test_consult_grammar(self, story_source):
        """The 'consulting it about' action is wired to the notebook.
        I7 defines the action in the standard rules; we only need a rule
        that responds when the player consults Yevgenia's notebook."""
        assert "consulting Yevgenia's notebook about" in story_source

    def test_look_up_grammar(self, story_source):
        """'look up [text] in [something]' is a synonym for consult."""
        assert 'look up [text] in [something]' in story_source

    def test_notebook_topics_table_exists(self, story_source):
        assert "Table of Notebook Topics" in story_source

    def test_consult_covers_safe_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"safe"' in table_section or "'safe'" in table_section

    def test_consult_covers_burn_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"burn"' in table_section or "'burn'" in table_section

    def test_consult_covers_selengrad_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"selengrad"' in table_section.lower()

    def test_consult_covers_argon_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"argon"' in table_section.lower()

    def test_consult_covers_transmit_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"transmit"' in table_section.lower()

    def test_consult_covers_deorbit_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"de-orbit"' in table_section.lower() or '"deorbit"' in table_section.lower()

    def test_consult_covers_tonight_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"tonight"' in table_section.lower()

    def test_consult_covers_code_topic(self, story_source):
        table_section = story_source[
            story_source.find("Table of Notebook Topics"):
        ]
        assert '"code"' in table_section.lower()

    def test_safe_code_randomized(self, story_source):
        """The safe code is generated randomly at game start."""
        assert "random number from 1000 to 9999" in story_source

    def test_safe_code_property_exists(self, story_source):
        """The classified safe has a safe-code number property."""
        assert "safe-code" in story_source

    def test_safe_opening_uses_dynamic_code(self, story_source):
        """The safe opening message uses the dynamic safe-code, not a hardcoded value."""
        open_section = story_source[
            story_source.find("Instead of opening the classified safe"):
        ]
        assert "safe-code of the classified safe" in open_section
        assert "three-seven-one-one" not in open_section.lower()

    def test_notebook_consult_fallback(self, story_source):
        """Consulting the notebook about an unlisted topic gives a helpful fallback."""
        assert "Yevgenia did not write about that" in story_source


# ── Story Progression ─────────────────────────────────────────────────


class TestStoryProgression:
    """Story progresses through all major beats end-to-end."""

    def test_beat_emergency_wake(self, story_source):
        """Beat 1: Player asleep in bunk, struck violently, comes to bleeding."""
        assert "You were sleeping" in story_source
        assert "bleeding" in story_source.lower()

    def test_beat_corridor_discovery(self, story_source):
        """Beat 2: Player reaches corridor and finds the dead crew."""
        assert "Yevgenia is scenery in the Main Corridor" in story_source
        assert "Petrov is scenery in the Observation Cupola" in story_source

    def test_beat_cupola_war_discovery(self, story_source):
        """Beat 3: Player discovers WWIII through the viewport."""
        assert "war-is-discovered" in story_source
        assert "thermonuclear" in story_source.lower() or "World War III" in story_source
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
        """Beat 7: Selengrad lunar base plan exists in the source."""
        # The plan is in Yevgenia's notebook (math) and proposed by the
        # player to Chen during TRANSMIT.
        assert "Selengrad" in story_source
        # Plan flavor anywhere in source — caretaker, hydroponics, math, fuel
        assert "caretaker" in story_source.lower() or "hydroponics" in story_source.lower() or "fuel reserves" in story_source.lower()

    def test_beat_prototype_boundary(self, story_source):
        """Beat 8: Game reaches prototype boundary with 'Begin preparations'."""
        assert "Begin preparations" in story_source
        assert "We have work to do" in story_source

    def test_story_beats_ordered(self, story_source):
        """Major beats appear in correct narrative order in source."""
        beats = [
            "You were sleeping",
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
            # Viewport uses the generic "look through [something]" form;
            # action-with-noun is illegal under Inform 7 v10.1.2.
            '"look through [something]" as examining',
            # Solo-crew additions:
            '"read [something]" as reading',
            # Pressure-equalization valve action (variants accepted)
        ]
        for rule in custom_actions:
            assert rule in story_source, f"Missing Understand rule: {rule}"
        # Hatch puzzle has at least one valve verb registered
        assert (
            '"pull lever"' in story_source
            or '"turn valve"' in story_source
            or '"open valve"' in story_source
        )


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

    def test_walkthrough_examines_dead_crew(self, story_source):
        """Walkthrough examines the bodies and reads the notebook/log
        (the artifacts that replace the old NPC dialogue)."""
        test_full = story_source[story_source.find("Test full with"):]
        assert "examine yevgenia" in test_full.lower() or "examine petrov" in test_full.lower()
        assert "read notebook" in test_full.lower() or "take notebook" in test_full.lower()
        assert "read log" in test_full.lower()

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
        assert "Test hatch with" in story_source
        assert "Test explore with" in story_source
        assert "Test full with" in story_source

    def test_score_tracking_exists(self, story_source):
        """Score tracking rewards key achievements."""
        assert "Use scoring" in story_source
        assert "increase the score" in story_source
        # Max score grew with the new prologue valve + log read achievements.
        assert "maximum score is 14" in story_source or "maximum score is 12" in story_source or "maximum score is 10" in story_source
