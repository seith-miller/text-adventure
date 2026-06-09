"""Tests for the Argon-87 Act 1 awareness cues (issue #114).

Across 8 playtest sessions on 2026-04-27, zero agents tried to engage
the station AI because the prose gave no signal that the AI existed.
Part 9B (from PR #68) already wires TALK TO ARGON / ASK ARGON ABOUT X
to the AI-PROMPT routing; this issue is the prose surface only. Three
cues layer: the Command Module description, the LOOK PORT face, and a
first-entry corridor speaker line.

These tests work at the source-string level since the Inform compiler
isn't available in CI. See tests/test_inform7_story.py for the parallel
pattern.
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
    def test_command_module_description_names_argon_monitor(self, story_source):
        idx = story_source.find("The Command Module is north of the Main Corridor.")
        assert idx != -1, "Command Module room definition not found"
        snippet = story_source[idx:idx + 1500]
        assert "ARGON-87" in snippet, "Command Module description does not name ARGON-87"
        assert "monitor" in snippet.lower(), "Command Module description does not mention the monitor"

    def test_command_module_port_face_describes_argon_monitor(self, story_source):
        idx = story_source.find("Instead of examining west when the location is the Command Module:")
        assert idx != -1, "Command Module port face rule not found"
        snippet = story_source[idx:idx + 1200]
        assert "ARGON-87" in snippet, "Command Module port face does not name ARGON-87"
        assert "АРГОН-87" in snippet, "Command Module port face does not include the Cyrillic plate"

    def test_main_corridor_speaker_cue_exists(self, story_source):
        assert "Argon-corridor-cue-shown" in story_source, "Main Corridor cue truth state not declared"
        assert "I am still here, comrade" in story_source, "Main Corridor speaker line is missing"
        assert "When you can hear me, I will hear you" in story_source, "Main Corridor speaker line is missing the second clause"

    def test_main_corridor_cue_fires_once(self, story_source):
        assert (
            "Every turn when the player is in the Main Corridor and argon-corridor-cue-shown is false"
            in story_source
        ), "Main Corridor cue is not gated to first entry"
        assert "now argon-corridor-cue-shown is true" in story_source, (
            "Main Corridor cue does not flip its gate after firing"
        )


class TestArgonMonitorScenery:
    def test_argon_monitor_is_scenery(self, story_source):
        assert (
            "The argon monitor is scenery in the Command Module" in story_source
        ), "ARGON-87 monitor is not scenery in the Command Module"

    def test_argon_monitor_understand_verbs(self, story_source):
        idx = story_source.find("The argon monitor is scenery")
        assert idx != -1
        snippet = story_source[idx:idx + 600]
        for verb in ['"monitor"', '"screen"', '"brass plate"']:
            assert verb in snippet, f"argon monitor missing Understand verb: {verb}"

    def test_argon_monitor_printed_name(self, story_source):
        # Apostrophe uses the [apostrophe] substitution so Inform 7's
        # typographic-quote handling doesn't turn the ' after the digit
        # into a stray double-quote at render time (#209).
        assert (
            'The printed name of the argon monitor is "ARGON-87[apostrophe]s monitor"'
            in story_source
        )

    def test_argon_monitor_does_not_grab_bare_argon(self, story_source):
        """The monitor scenery must not claim the bare word 'argon' as
        an Understand synonym. Part 9B's TALK TO ARGON / ASK ARGON
        ABOUT X actions parse 'argon' as part of their command grammar,
        and a competing noun would create resolver collisions."""
        idx = story_source.find("The argon monitor is scenery")
        assert idx != -1
        # Find the Understand line that follows.
        end = story_source.find("\n\n", idx)
        block = story_source[idx:end]
        assert '"argon"' not in block, (
            "argon monitor declares bare 'argon' as Understand synonym; "
            "this collides with Part 9B's verb grammar"
        )


class TestPart9BUntouched:
    """Salvage constraint: Part 9B's AI-PROMPT routing (from PR #68)
    must remain intact. The new prose work layers on top, it does not
    replace the verb wiring."""

    def test_part_9b_grammar_still_present(self, story_source):
        assert "Part 9B - Argon-87 grammar (m8 in-game runtime)" in story_source
        assert "Talking to argon is an action applying to nothing" in story_source
        assert "Asking argon about is an action applying to one topic" in story_source
        assert "[bracket]AI-PROMPT: topic=general[close bracket]" in story_source
        assert "[bracket]AI-PROMPT: topic=[the topic understood][close bracket]" in story_source


class TestProseStyleCompliance:
    PART_9D_START = "Part 9D - Argon-87 awareness cues (prose)"
    PART_10_START = "Part 10 - Score Tracking"

    def _argon_prose_block(self, story_source):
        start = story_source.find(self.PART_9D_START)
        end = story_source.find(self.PART_10_START)
        assert start != -1 and end != -1 and end > start, "Could not isolate Part 9D"
        return story_source[start:end]

    def test_no_em_dashes_in_argon_block(self, story_source):
        block = self._argon_prose_block(story_source)
        assert "—" not in block, "Em-dash (—) found in Argon prose block"
        assert "--" not in block, "ASCII em-dash surrogate (--) found in Argon prose block"

    def test_no_em_dash_in_command_module_argon_addition(self, story_source):
        # Apostrophe via [apostrophe] substitution (#209).
        idx = story_source.find("On the port wall, ARGON-87[apostrophe]s monitor")
        assert idx != -1, "Command Module ARGON-87 monitor mention not found"
        snippet = story_source[idx:idx + 80]
        assert "—" not in snippet, "Em-dash present in ARGON-87 monitor mention"

    def test_argon_voice_is_formal_soviet(self, story_source):
        block = self._argon_prose_block(story_source)
        assert "comrade" in block.lower(), "ARGON-87's voice does not use the 'comrade' address"
