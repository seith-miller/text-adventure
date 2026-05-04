"""Tests for console interaction verbs with diagnostic refusals (issue #117).

Validates that story.ni defines an 'operating' action covering USE,
ACTIVATE, INTERACT WITH, POWER ON, and TURN ON for consoles, and that
unpowered consoles produce diagnostic refusals naming the missing
prerequisite.
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


# ── Action Definition ─────────────────────────────────────────────────


class TestOperatingActionExists:
    """The 'operating' action is declared and wired to the required verbs."""

    def test_operating_action_declared(self, story_source):
        assert "Operating is an action applying to one thing" in story_source

    def test_use_understood(self, story_source):
        assert 'Understand "use [something]" as operating' in story_source

    def test_activate_understood(self, story_source):
        assert 'Understand "activate [something]" as operating' in story_source

    def test_interact_with_understood(self, story_source):
        assert 'Understand "interact with [something]" as operating' in story_source

    def test_power_on_understood(self, story_source):
        assert 'Understand "power on [something]" as operating' in story_source

    def test_turn_on_redirects_deorbit(self, story_source):
        """TURN ON (switching on) redirects to operating for the deorbit console."""
        assert "Instead of switching on the deorbit console" in story_source
        assert "try operating the deorbit console" in story_source

    def test_turn_on_redirects_status(self, story_source):
        """TURN ON (switching on) redirects to operating for the status console."""
        assert "Instead of switching on the status console" in story_source
        assert "try operating the status console" in story_source

    def test_turn_on_redirects_fire_control(self, story_source):
        """TURN ON (switching on) redirects to operating for the fire-control console."""
        assert "Instead of switching on the fire-control console" in story_source
        assert "try operating the fire-control console" in story_source


# ── Unpowered Refusals ────────────────────────────────────────────────


class TestUnpoweredRefusals:
    """Each console has a diagnostic refusal when unpowered."""

    def test_deorbit_unpowered_refusal_exists(self, story_source):
        assert "operating the deorbit console when power-is-restored is false" in story_source

    def test_deorbit_refusal_mentions_power(self, story_source):
        """The deorbit refusal tells the player power is missing."""
        # Find the refusal block
        idx = story_source.find("operating the deorbit console when power-is-restored is false")
        assert idx != -1
        block = story_source[idx:idx + 500]
        assert "power" in block.lower()

    def test_deorbit_refusal_mentions_authorization(self, story_source):
        """The deorbit refusal mentions the Command Module authorization prerequisite."""
        idx = story_source.find("operating the deorbit console when power-is-restored is false")
        block = story_source[idx:idx + 500]
        assert "authorization" in block.lower() or "status loop" in block.lower()

    def test_status_console_unpowered_refusal_exists(self, story_source):
        assert "operating the status console when power-is-restored is false" in story_source

    def test_status_console_refusal_mentions_power_bus(self, story_source):
        """The status console refusal tells the player about the power bus."""
        idx = story_source.find("operating the status console when power-is-restored is false")
        assert idx != -1
        block = story_source[idx:idx + 500]
        assert "power" in block.lower()
        assert "bus" in block.lower()

    def test_fire_control_unpowered_refusal_exists(self, story_source):
        assert "operating the fire-control console when the fire-control console is unpowered" in story_source

    def test_fire_control_refusal_is_diagnostic(self, story_source):
        """The fire-control refusal names what's wrong."""
        idx = story_source.find("operating the fire-control console when the fire-control console is unpowered")
        assert idx != -1
        block = story_source[idx:idx + 500]
        assert "dark" in block.lower() or "power" in block.lower()


# ── Powered Responses ─────────────────────────────────────────────────


class TestPoweredResponses:
    """Each console has a meaningful response when powered."""

    def test_status_console_powered_response(self, story_source):
        assert "operating the status console when power-is-restored is true" in story_source

    def test_deorbit_console_powered_response(self, story_source):
        assert "operating the deorbit console when power-is-restored is true" in story_source

    def test_fire_control_powered_response(self, story_source):
        assert "operating the fire-control console when the fire-control console is powered" in story_source


# ── Prose Quality ─────────────────────────────────────────────────────


class TestRefusalProseQuality:
    """Refusal prose follows writing-style.md rules."""

    def test_no_em_dashes_in_refusals(self, story_source):
        """No em-dashes allowed per writing-style.md."""
        # Extract all operating-related blocks
        parts = story_source.split("Instead of operating")
        for part in parts[1:]:  # skip first (before any operating rule)
            block = part[:500]
            assert "\u2014" not in block, f"Em-dash found in operating rule: {block[:80]}"
            assert " -- " not in block, f"Double-dash found in operating rule: {block[:80]}"

    def test_refusals_are_not_generic(self, story_source):
        """Refusals must not use generic Inform 7 default text."""
        generic_phrases = [
            "That's not a verb I recognise",
            "I didn't understand that sentence",
            "It isn't something you can switch",
            "It is fixed in place",
        ]
        # These should NOT appear as our response text
        for rule_start in ["operating the deorbit console when power-is-restored is false",
                           "operating the status console when power-is-restored is false"]:
            idx = story_source.find(rule_start)
            if idx != -1:
                block = story_source[idx:idx + 500]
                for phrase in generic_phrases:
                    assert phrase not in block, f"Generic phrase '{phrase}' found in refusal"
