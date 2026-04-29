"""Tests for examinable shadow objects (issue #116).

Validates that prose-mentioned but previously non-interactive objects
now exist as scenery with descriptions and take-refusal rules.
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


# ── Crew Quarters scenery ────────────────────────────────────────────


class TestBunks:
    """Bunks are mentioned in the Crew Quarters prose and must be examinable."""

    def test_bunks_are_scenery(self, story_source):
        assert "bunks are scenery in the Crew Quarters" in story_source

    def test_bunks_understand_synonyms(self, story_source):
        assert '"bunk"' in story_source
        assert '"fourth bunk"' in story_source

    def test_bunks_have_description(self, story_source):
        assert "Four bunks in their slots" in story_source

    def test_bunks_take_refused(self, story_source):
        assert "Instead of taking the bunks" in story_source


# ── Main Corridor floating debris scenery ────────────────────────────


class TestClipboard:
    """The clipboard is mentioned in corridor prose and must be examinable."""

    def test_clipboard_is_scenery(self, story_source):
        assert "clipboard is scenery in the Main Corridor" in story_source

    def test_clipboard_understand(self, story_source):
        assert '"clipboard"' in story_source

    def test_clipboard_description(self, story_source):
        assert "clipboard with the day's flight plan" in story_source

    def test_clipboard_take_refused(self, story_source):
        assert "Instead of taking the drifting clipboard" in story_source


class TestFlightManual:
    """The flight manual is mentioned in corridor prose and must be examinable."""

    def test_flight_manual_is_scenery(self, story_source):
        assert "flight manual is scenery in the Main Corridor" in story_source

    def test_flight_manual_understand(self, story_source):
        assert '"flight manual"' in story_source

    def test_flight_manual_description(self, story_source):
        assert "emergency repressurization" in story_source

    def test_flight_manual_take_refused(self, story_source):
        assert "Instead of taking the drifting flight manual" in story_source


class TestMug:
    """The mug is mentioned in corridor prose and must be examinable."""

    def test_mug_is_scenery(self, story_source):
        assert "mug is scenery in the Main Corridor" in story_source

    def test_mug_understand_synonyms(self, story_source):
        assert '"mug"' in story_source
        assert '"drinking bulb"' in story_source

    def test_mug_description(self, story_source):
        assert "Half-full of cold tea" in story_source

    def test_mug_take_refused(self, story_source):
        assert "Instead of taking the drifting mug" in story_source


# ── Main Corridor cables scenery ─────────────────────────────────────


class TestCables:
    """Cables near the maintenance panel must be examinable."""

    def test_cables_are_scenery(self, story_source):
        assert "cables are scenery in the Main Corridor" in story_source

    def test_cables_understand_synonyms(self, story_source):
        assert '"cables"' in story_source
        assert '"cabling"' in story_source

    def test_cables_description(self, story_source):
        assert "tangle of cabling" in story_source

    def test_cables_take_refused(self, story_source):
        assert "Instead of taking the loose cables" in story_source


# ── Screwdriver scenery (Yevgenia's body) ────────────────────────────


class TestScrewdriver:
    """The screwdriver mentioned in Yevgenia's description must be examinable."""

    def test_screwdriver_is_scenery(self, story_source):
        assert "screwdriver is scenery in the Main Corridor" in story_source

    def test_screwdriver_understand(self, story_source):
        assert '"screwdriver"' in story_source

    def test_screwdriver_description(self, story_source):
        assert "holds it the way you hold a tool" in story_source

    def test_screwdriver_take_refused(self, story_source):
        assert "Instead of taking the held screwdriver" in story_source


# ── Cupola viewport / earth synonyms ────────────────────────────────


class TestEarthViewport:
    """'examine earth' must resolve to the viewport in the Cupola."""

    def test_viewport_is_scenery(self, story_source):
        assert "viewport is scenery in the Observation Cupola" in story_source

    def test_earth_understood_as_viewport(self, story_source):
        # The Understand clause must map "earth" to the viewport
        assert '"earth"' in story_source

    def test_nightside_understood_as_viewport(self, story_source):
        assert '"nightside"' in story_source

    def test_viewport_examine_triggers_war_discovery(self, story_source):
        """The viewport examine rule should still trigger the war discovery."""
        assert "examining the viewport" in story_source
        assert "war-is-discovered" in story_source


# ── Command Module control panels ────────────────────────────────────


class TestControlPanels:
    """Control panels must have 'panels' synonym and updated description."""

    def test_control_panels_are_scenery(self, story_source):
        assert "control panels are scenery in the Command Module" in story_source

    def test_panels_synonym(self, story_source):
        # Must understand bare "panels" so 'examine panels' works
        src_lower = story_source.lower()
        assert '"panels"' in src_lower

    def test_control_panels_unpowered_description(self, story_source):
        assert "Every panel is dead" in story_source

    def test_control_panels_powered_description(self, story_source):
        assert "working console on the main bus" in story_source
