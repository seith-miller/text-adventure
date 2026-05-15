"""Tests for the Argon-87 Act 1 cue (issue #114).

Across 8 playtest sessions on 2026-04-27, zero agents tried to engage
the station AI because the prose gave no signal that the AI existed.
This file validates that the Inform 7 source now plants an explicit
ARGON-87 cue early in Act 1, alongside basic interaction grammar so
the cue lands meaningfully when the player follows up.

The compiler isn't available in this CI environment, so these tests
work at the source-string level. See tests/test_inform7_story.py for
the parallel pattern.
"""

import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_NI = os.path.join(ROOT, "game", "inform", "Source", "story.ni")


@pytest.fixture(scope="module")
def story_source():
    with open(STORY_NI) as f:
        return f.read()


class TestArgonProseCues:
    """The player must encounter ARGON-87 in prose during the first
    fifteen turns of a fresh playthrough. Two cues are layered: the
    Command Module description names ARGON-87's monitor on the port
    wall, and the first entry to the Main Corridor triggers a
    capacitor-burst speaker line in his voice."""

    def test_command_module_description_names_argon_monitor(self, story_source):
        """The Command Module room description references ARGON-87's
        monitor by name. A player who walks into the room sees it
        mentioned without needing any verb."""
        # Locate the Command Module description and assert ARGON-87 is in it.
        idx = story_source.find("The Command Module is north of the Main Corridor.")
        assert idx != -1, "Command Module room definition not found"
        # Description is the quoted block that follows.
        snippet = story_source[idx:idx + 1500]
        assert "ARGON-87" in snippet, (
            "Command Module description does not name ARGON-87"
        )
        assert "monitor" in snippet.lower(), (
            "Command Module description does not mention the monitor artifact"
        )

    def test_command_module_port_face_describes_argon_monitor(self, story_source):
        """LOOK PORT in the Command Module exposes the monitor as a
        physical artifact on the port wall."""
        # The port face description for the Command Module.
        idx = story_source.find(
            "Instead of examining west when the location is the Command Module:"
        )
        assert idx != -1, "Command Module port face rule not found"
        snippet = story_source[idx:idx + 1200]
        assert "ARGON-87" in snippet, (
            "Command Module port face description does not name ARGON-87"
        )

    def test_main_corridor_speaker_cue_exists(self, story_source):
        """The first time the player stands in the Main Corridor, an
        Every-turn rule prints ARGON-87's voice once."""
        assert "Argon-corridor-cue-shown" in story_source, (
            "Main Corridor cue truth state not declared"
        )
        assert "I am still here, comrade" in story_source, (
            "Main Corridor speaker line is missing"
        )
        assert "When you can hear me, I will hear you" in story_source, (
            "Main Corridor speaker line is missing the second clause"
        )

    def test_main_corridor_cue_fires_once(self, story_source):
        """The cue is gated on the truth state so the line only prints
        on the player's first visit, not every turn afterward."""
        assert (
            "Every turn when the player is in the Main Corridor and argon-corridor-cue-shown is false"
            in story_source
        ), "Main Corridor cue is not gated to first entry"
        assert "now argon-corridor-cue-shown is true" in story_source, (
            "Main Corridor cue does not flip its gate after firing"
        )


class TestArgonInteractionGrammar:
    """The cue is hollow if the player tries TALK TO ARGON and gets the
    parser default. Argon must be addressable, talkable, and askable."""

    def test_argon_is_a_backdrop_everywhere(self, story_source):
        """ARGON-87 lives in the hull, not in a single room. Backdrop
        + everywhere makes him resolvable from any module the player
        is standing in."""
        assert "Argon is a backdrop" in story_source, (
            "ARGON-87 is not declared as a backdrop"
        )
        assert "Argon is everywhere" in story_source, (
            "ARGON-87 backdrop is not placed everywhere"
        )

    def test_argon_understand_synonyms(self, story_source):
        """The player can refer to him as argon, argon-87, the AI,
        the station computer, etc."""
        for synonym in ['"argon"', '"argon-87"', '"ai"', '"station ai"', '"station computer"']:
            assert synonym in story_source, (
                f"ARGON-87 missing Understand synonym: {synonym}"
            )

    def test_argon_printed_name(self, story_source):
        """The player sees ARGON-87 in caps with the hyphen and number,
        even though the internal Inform identifier is plain."""
        assert 'The printed name of Argon is "ARGON-87"' in story_source

    def test_talk_to_argon_has_response(self, story_source):
        """TALK TO ARGON has a dedicated Instead rule, so it does not
        fall through to the catch-all 'no one here to speak with'."""
        assert "Instead of talking to Argon:" in story_source

    def test_talk_to_argon_response_branches_on_power(self, story_source):
        """The response differs by whether power has been restored.
        Offline early, listening once the bus is back."""
        idx = story_source.find("Instead of talking to Argon:")
        assert idx != -1
        snippet = story_source[idx:idx + 1000]
        assert "power-is-restored is false" in snippet, (
            "Talk-to-Argon response does not branch on power state"
        )

    def test_ask_argon_about_grammar_exists(self, story_source):
        """ASK ARGON ABOUT X is parsed via a topic-only action so the
        parser does not require ARGON-87 to be a person."""
        assert "Asking-the-station is an action applying to one topic" in story_source
        assert 'Understand "ask argon about [text]" as asking-the-station' in story_source
        assert 'Understand "ask station about [text]" as asking-the-station' in story_source


class TestArgonMonitorScenery:
    """The physical monitor in the Command Module is a separate
    examinable object so the player can EXAMINE MONITOR distinct
    from EXAMINE ARGON."""

    def test_argon_monitor_is_scenery(self, story_source):
        assert (
            "The argon monitor is scenery in the Command Module"
            in story_source
        ), "ARGON-87 monitor is not scenery in the Command Module"

    def test_argon_monitor_understand_verbs(self, story_source):
        """Verbs scoped to the physical artifact (monitor / screen /
        brass plate) so EXAMINE MONITOR resolves without colliding
        with the ARGON-87 backdrop's own Understand list."""
        idx = story_source.find("The argon monitor is scenery")
        assert idx != -1
        snippet = story_source[idx:idx + 600]
        for verb in ['"monitor"', '"screen"']:
            assert verb in snippet, (
                f"argon monitor missing Understand verb: {verb}"
            )

    def test_argon_monitor_printed_name(self, story_source):
        assert (
            'The printed name of the argon monitor is "ARGON-87\'s monitor"'
            in story_source
        )


class TestProseStyleCompliance:
    """docs/writing-style.md is the ground truth for prose. The Argon
    cue must follow the same rules: no em-dashes, mystic-or-elemental
    register, calm Soviet voice for ARGON-87 himself."""

    ARGON_BLOCK_MARKERS = (
        "Part 9B - Argon-87 AI Presence",
        "Part 10 - Score Tracking",
    )

    def _argon_block(self, story_source):
        start = story_source.find(self.ARGON_BLOCK_MARKERS[0])
        end = story_source.find(self.ARGON_BLOCK_MARKERS[1])
        assert start != -1 and end != -1 and end > start, (
            "Could not isolate Part 9B (Argon) block"
        )
        return story_source[start:end]

    def test_no_em_dashes_in_argon_block(self, story_source):
        """No em-dashes anywhere in the new Argon prose. Per
        docs/writing-style.md this is non-negotiable."""
        block = self._argon_block(story_source)
        assert "—" not in block, "Em-dash (—) found in Argon prose block"
        # Two consecutive ASCII hyphens are also forbidden as em-dash
        # surrogate. (The map-command ASCII art is in Part 3B, not this
        # block, so it does not show up here.)
        assert "--" not in block, (
            "ASCII em-dash surrogate (--) found in Argon prose block"
        )

    def test_no_em_dash_in_command_module_argon_addition(self, story_source):
        """The added 'On the port wall, ARGON-87's monitor.' fragment
        in the Command Module description must use a period, not the
        em-dash that appeared in issue #114's draft text."""
        idx = story_source.find("On the port wall, ARGON-87's monitor")
        assert idx != -1, "Command Module ARGON-87 monitor mention not found"
        snippet = story_source[idx:idx + 80]
        assert "—" not in snippet, "Em-dash present in ARGON-87 monitor mention"

    def test_argon_voice_is_formal_soviet(self, story_source):
        """ARGON-87's spoken line addresses the player as 'comrade'
        and uses the calm formal register the persona doc specifies."""
        block = self._argon_block(story_source)
        assert "comrade" in block.lower(), (
            "ARGON-87's voice does not use the 'comrade' address"
        )
