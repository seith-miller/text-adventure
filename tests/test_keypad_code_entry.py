"""Tests for keypad code-entry grammar (issue #115).

Validates that the Inform 7 source contains:
- A generic code-entering action with Understand grammar
- Grammar for 'enter NNNN on <thing>', 'type NNNN on <thing>',
  'enter code NNNN', and bare number forms
- Safe-code property on the classified safe, randomized at game start
- Wrong-code feedback message
- Correct-code opens the armament bay
- Spoken-digits display phrase
- Keypad synonym for the classified safe
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


class TestCodeEntryAction:
    """The code-entering action exists and is properly defined."""

    def test_action_defined(self, story_source):
        """Code-entering action applies to a number and a thing."""
        assert "Code-entering it on is an action applying to one number and one thing" in story_source

    def test_enter_number_on_grammar(self, story_source):
        """'enter [number] on [something]' grammar exists."""
        assert '"enter [number] on [something]" as code-entering it on' in story_source

    def test_type_number_on_grammar(self, story_source):
        """'type [number] on [something]' grammar exists."""
        assert '"type [number] on [something]" as code-entering it on' in story_source

    def test_enter_code_number_on_grammar(self, story_source):
        """'enter code [number] on [something]' grammar exists."""
        assert '"enter code [number] on [something]" as code-entering it on' in story_source

    def test_type_code_number_on_grammar(self, story_source):
        """'type code [number] on [something]' grammar exists."""
        assert '"type code [number] on [something]" as code-entering it on' in story_source

    def test_bare_enter_code_grammar(self, story_source):
        """Bare 'enter code [number]' targets the safe."""
        assert '"enter code [number]" as code-entering it on the safe' in story_source

    def test_bare_enter_number_grammar(self, story_source):
        """Bare 'enter [number]' targets the safe."""
        assert '"enter [number]" as code-entering it on the safe' in story_source

    def test_bare_type_number_grammar(self, story_source):
        """Bare 'type [number]' targets the safe."""
        assert '"type [number]" as code-entering it on the safe' in story_source

    def test_range_check(self, story_source):
        """Codes outside 1-9999 are rejected."""
        assert "N < 1 or N > 9999" in story_source
        assert "four-digit codes only" in story_source


class TestSafeCodeProperty:
    """The classified safe has a dynamic code randomized each playthrough."""

    def test_safe_has_code_property(self, story_source):
        """The safe has a number property called safe-code."""
        assert "classified safe has a number called the safe-code" in story_source

    def test_safe_code_randomized(self, story_source):
        """Safe code is randomized 1000-9999 at game start."""
        assert "safe-code of the classified safe is a random number from 1000 to 9999" in story_source

    def test_safe_code_in_when_play_begins(self, story_source):
        """Randomization happens in the 'When play begins' rule."""
        when_play = story_source[story_source.find("When play begins"):]
        assert "safe-code of the classified safe is a random number" in when_play


class TestSafeCodeComparison:
    """Entered code is compared against the safe's per-game code."""

    def test_correct_code_opens_armament(self, story_source):
        """Correct code sets armament-bay-unlocked."""
        assert "N is the safe-code of the classified safe" in story_source
        assert "now armament-bay-unlocked is true" in story_source

    def test_wrong_code_message(self, story_source):
        """Wrong code shows 'The keypad blinks once. Wrong code.'"""
        assert "The keypad blinks once. Wrong code." in story_source

    def test_already_open_message(self, story_source):
        """If safe already opened, code entry says so."""
        # The code-entering rule checks armament-bay-unlocked.
        # Inform 7 binds the rule with "a number on the classified safe"
        # rather than "it on the classified safe".
        idx = story_source.find("code-entering a number on the classified safe")
        assert idx != -1, "code-entering rule for the safe not found"
        code_entry_section = story_source[idx:idx + 1500]
        assert "armament-bay-unlocked is true" in code_entry_section

    def test_dynamic_code_in_success_message(self, story_source):
        """Success message uses dynamic spoken digits, not hardcoded."""
        assert "safe-code of the classified safe as spoken digits" in story_source


class TestSpokenDigits:
    """The spoken-digits phrase formats a number as D-D-D-D."""

    def test_spoken_digits_phrase_exists(self, story_source):
        """The 'say N as spoken digits' phrase exists."""
        assert "To say (N - a number) as spoken digits" in story_source

    def test_spoken_digits_decomposes(self, story_source):
        """Spoken digits decomposes into four individual digits."""
        assert "D4" in story_source
        assert "D3" in story_source
        assert "D2" in story_source
        assert "D1" in story_source
        assert '"[D4]-[D3]-[D2]-[D1]"' in story_source


class TestKeypadSynonym:
    """'keypad' is understood as the classified safe."""

    def test_keypad_synonym(self, story_source):
        """'keypad' is a synonym for the classified safe."""
        assert '"keypad" as the classified safe' in story_source


class TestOpeningSafeStillWorks:
    """The 'open safe' fallback still works for players who have the code."""

    def test_open_safe_rule_exists(self, story_source):
        """Instead of opening the classified safe rule exists."""
        assert "Instead of opening the classified safe" in story_source

    def test_open_safe_requires_log(self, story_source):
        """Opening the safe still requires petrov-log-read."""
        open_section = story_source[story_source.find("Instead of opening the classified safe"):]
        assert "petrov-log-read is false" in open_section

    def test_open_safe_uses_dynamic_code(self, story_source):
        """Opening the safe uses dynamic spoken digits."""
        open_section = story_source[story_source.find("Instead of opening the classified safe"):]
        assert "safe-code of the classified safe as spoken digits" in open_section


class TestGenericDesign:
    """The action is generic — works for any keypad-locked thing, not just the safe."""

    def test_action_applies_to_any_thing(self, story_source):
        """The action takes [something], not a specific object."""
        assert '"enter [number] on [something]"' in story_source
        assert '"type [number] on [something]"' in story_source

    def test_check_rule_is_generic(self, story_source):
        """The range-check rule applies to code-entering, not a specific object."""
        assert "Check code-entering it on" in story_source
