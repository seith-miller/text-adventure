"""Tests for the opening scene Ink source (kept as reference).

The project has migrated from Ink to Inform 7. These tests validate that
the original Ink source files are preserved as reference material. Tests
that require Ink compilation are skipped since build:story now targets
Inform 7. See test_inform7_pipeline.py for the new pipeline tests.
"""

import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENING_INK = os.path.join(ROOT, "game", "story", "opening.ink")


def test_opening_ink_exists():
    """opening.ink file exists in game/story/ as reference."""
    assert os.path.isfile(OPENING_INK), "game/story/opening.ink not found"


def test_opening_ink_has_content():
    """opening.ink contains the original story content."""
    with open(OPENING_INK) as f:
        content = f.read()
    assert "oxygen" in content, "Expected oxygen variable in opening.ink"
    assert "Mir-2" in content or "MIR" in content, "Expected station reference"
    assert len(content) > 1000, "opening.ink seems too short to be the full scene"


INK_COMPILE_SKIP = "Ink compilation skipped — pipeline migrated to Inform 7"


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_opening_compiles():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_compiled_json_is_valid():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_compiled_json_loadable_by_inkjs():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_global_variables_exist():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_no_dead_ends_path_search():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_ascii_tags_emitted():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_oxygen_decreases():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_flashlight_acquired():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_branching_paths_exist():
    pass


@pytest.mark.skip(reason=INK_COMPILE_SKIP)
def test_scene_ends_at_clear_boundary():
    pass
