"""E5 timer-guard tests: source-level validation of climax guard and dispatcher.

Validates that the Inform 7 source contains:
- player-has-committed-climax derived check
- chose-descent and cannon-fired truth states
- Oxygen timer guarded by climax commitment
- E5 dispatcher action with oxygen sub-variant
"""

import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_NI = os.path.join(ROOT, "game", "inform", "Source", "story.ni")


@pytest.fixture(scope="module")
def story_source():
    """Load the Inform 7 source file."""
    with open(STORY_NI) as f:
        return f.read()


class TestClimaxCommitmentStates:
    """Truth states for climax commitment exist and are initialized false."""

    def test_chose_descent_exists(self, story_source):
        assert "Chose-descent is a truth state that varies" in story_source

    def test_chose_descent_default_false(self, story_source):
        assert "Chose-descent is false" in story_source

    def test_cannon_fired_exists(self, story_source):
        assert "Cannon-fired is a truth state that varies" in story_source

    def test_cannon_fired_default_false(self, story_source):
        assert "Cannon-fired is false" in story_source

    def test_responded_to_americans_still_exists(self, story_source):
        assert "Responded-to-americans is a truth state that varies" in story_source


class TestPlayerHasCommittedClimax:
    """Derived check combines all three climax truth states."""

    def test_derived_check_exists(self, story_source):
        assert "player has committed climax" in story_source.lower()

    def test_checks_responded_to_americans(self, story_source):
        assert "responded-to-americans is true" in story_source.lower()

    def test_checks_chose_descent(self, story_source):
        assert "chose-descent is true" in story_source.lower()

    def test_checks_cannon_fired(self, story_source):
        assert "cannon-fired is true" in story_source.lower()


class TestOxygenTimerGuard:
    """Oxygen timer is guarded by climax commitment."""

    def test_oxygen_guarded_by_climax(self, story_source):
        """The every-turn rule checks climax before decreasing oxygen."""
        assert "player has committed climax" in story_source.lower()
        assert "decrease oxygen-level by 1" in story_source

    def test_oxygen_still_decreases_when_no_climax(self, story_source):
        """Oxygen depletion still fires for uncommitted players."""
        assert "decrease oxygen-level by 1" in story_source


class TestE5Dispatcher:
    """E5 dispatcher action exists and handles oxygen sub-variant."""

    def test_dispatcher_action_exists(self, story_source):
        assert "E5 dispatching is an action applying to nothing" in story_source

    def test_oxygen_subvariant_triggers(self, story_source):
        assert "oxygen-level <= 0" in story_source.lower()

    def test_placeholder_prose_tagged(self, story_source):
        """Prose placeholder references issue #60."""
        assert "TODO prose: #60" in story_source

    def test_suffocation_ending(self, story_source):
        assert "suffocated" in story_source.lower()

    def test_e5_suffocate_key(self, story_source):
        """Dispatcher mentions the e5-suffocate key."""
        assert "e5-suffocate" in story_source.lower()
