"""M4 integration tests: Selengrad arc mechanics (issue #42).

Validates that the Selengrad arc mechanism is wired end-to-end:
- selengrad-prep-begun truth state set by TRANSMIT
- Oxygen timer suspended after prep begins
- D1 action (prepare selengrad) gated on selengrad-prep-begun
- D1 sub-choice: split fuel / give fuel (irreversible, mutually exclusive)
- E1 (arrival) / E2 (martyr) dispatch via every-turn counter
- All new prose is placeholder tagged [TODO prose: #55]
- Test scripts for both E1 and E2 paths exist
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


# ── Truth States ─────────────────────────────────────────────────────


class TestTruthStates:
    """All new truth states are declared and initialized."""

    def test_selengrad_prep_begun_declared(self, story_source):
        assert "Selengrad-prep-begun is a truth state that varies" in story_source

    def test_selengrad_prep_begun_initialized_false(self, story_source):
        assert "Selengrad-prep-begun is false" in story_source

    def test_chose_split_fuel_declared(self, story_source):
        assert "Chose-split-fuel is a truth state that varies" in story_source

    def test_chose_split_fuel_initialized_false(self, story_source):
        assert "Chose-split-fuel is false" in story_source

    def test_chose_martyr_declared(self, story_source):
        assert "Chose-martyr is a truth state that varies" in story_source

    def test_chose_martyr_initialized_false(self, story_source):
        assert "Chose-martyr is false" in story_source

    def test_fuel_choice_made_declared(self, story_source):
        assert "Fuel-choice-made is a truth state that varies" in story_source

    def test_fuel_choice_made_initialized_false(self, story_source):
        assert "Fuel-choice-made is false" in story_source

    def test_d1_counter_declared(self, story_source):
        assert "D1-counter is a number that varies" in story_source

    def test_d1_counter_initialized_zero(self, story_source):
        assert "D1-counter is 0" in story_source


# ── Selengrad-prep-begun is set by TRANSMIT ──────────────────────────


class TestPrepBegunSetByTransmit:
    """The selengrad-prep-begun flag is flipped in the Carry out transmitting rule."""

    def test_transmit_sets_prep_begun(self, story_source):
        """Carry out transmitting sets selengrad-prep-begun to true."""
        # Find the Carry out transmitting block
        carry_out_idx = story_source.find("Carry out transmitting:")
        assert carry_out_idx != -1, "Carry out transmitting rule not found"
        # Look for the flag set within a reasonable range
        block = story_source[carry_out_idx:carry_out_idx + 300]
        assert "now selengrad-prep-begun is true" in block


# ── Oxygen Timer Guard ───────────────────────────────────────────────


class TestOxygenTimerGuard:
    """The oxygen timer must not fire suffocation after TRANSMIT."""

    def test_oxygen_timer_guarded(self, story_source):
        """The oxygen every-turn rule's `when` clause halts during arcs."""
        # Find the oxygen timer rule (decrease oxygen-level).
        idx = story_source.find("decrease oxygen-level by 1")
        assert idx != -1, "Oxygen decrement rule not found"
        # The guard should appear in the `Every turn when ...:` clause
        # immediately before the decrement.
        block_start = story_source.rfind("Every turn when ", 0, idx)
        assert block_start != -1
        guard_block = story_source[block_start:idx]
        assert "selengrad-prep-begun is false" in guard_block, (
            "Oxygen timer must be guarded by selengrad-prep-begun check"
        )


# ── D1 Action: Prepare Selengrad ─────────────────────────────────────


class TestD1Action:
    """The D1 trigger action exists and is properly gated."""

    def test_preparing_selengrad_is_action(self, story_source):
        assert "Preparing selengrad is an action" in story_source

    def test_understand_prepare_selengrad(self, story_source):
        assert '"prepare selengrad" as preparing selengrad' in story_source

    def test_understand_begin_preparations(self, story_source):
        assert '"begin preparations" as preparing selengrad' in story_source

    def test_check_requires_command_module(self, story_source):
        """D1 action requires being in the Command Module."""
        check_idx = story_source.find("Check preparing selengrad:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 500]
        assert "player is not in the Command Module" in block

    def test_check_requires_prep_begun(self, story_source):
        """D1 action requires selengrad-prep-begun to be true."""
        check_idx = story_source.find("Check preparing selengrad:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 500]
        assert "selengrad-prep-begun is false" in block

    def test_check_blocks_after_choice(self, story_source):
        """D1 action blocked once fuel choice is made."""
        check_idx = story_source.find("Check preparing selengrad:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 500]
        assert "fuel-choice-made is true" in block

    def test_report_has_placeholder(self, story_source):
        """D1 report text includes placeholder tag."""
        report_idx = story_source.find("Report preparing selengrad:")
        assert report_idx != -1
        block = story_source[report_idx:report_idx + 600]
        assert "TODO prose: #55" in block

    def test_report_presents_choice(self, story_source):
        """D1 report text presents the split/give choice."""
        report_idx = story_source.find("Report preparing selengrad:")
        assert report_idx != -1
        block = story_source[report_idx:report_idx + 600]
        assert "SPLIT FUEL" in block
        assert "GIVE FUEL" in block


# ── D1 Sub-Choice: Split Fuel ────────────────────────────────────────


class TestSplitFuel:
    """The split fuel action exists and sets the correct state."""

    def test_splitting_fuel_is_action(self, story_source):
        assert "Splitting fuel is an action" in story_source

    def test_understand_split_fuel(self, story_source):
        assert '"split fuel" as splitting fuel' in story_source

    def test_check_requires_prep_begun(self, story_source):
        check_idx = story_source.find("Check splitting fuel:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 300]
        assert "selengrad-prep-begun is false" in block

    def test_check_blocks_after_choice(self, story_source):
        check_idx = story_source.find("Check splitting fuel:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 300]
        assert "fuel-choice-made is true" in block

    def test_carry_out_sets_split(self, story_source):
        carry_idx = story_source.find("Carry out splitting fuel:")
        assert carry_idx != -1
        block = story_source[carry_idx:carry_idx + 200]
        assert "now chose-split-fuel is true" in block

    def test_carry_out_sets_choice_made(self, story_source):
        carry_idx = story_source.find("Carry out splitting fuel:")
        assert carry_idx != -1
        block = story_source[carry_idx:carry_idx + 200]
        assert "now fuel-choice-made is true" in block

    def test_report_has_placeholder(self, story_source):
        report_idx = story_source.find("Report splitting fuel:")
        assert report_idx != -1
        block = story_source[report_idx:report_idx + 400]
        assert "TODO prose: #55" in block


# ── D1 Sub-Choice: Give Fuel (Martyr) ────────────────────────────────


class TestGiveFuel:
    """The give fuel action exists and sets the correct state."""

    def test_giving_fuel_is_action(self, story_source):
        assert "Giving fuel is an action" in story_source

    def test_understand_give_fuel(self, story_source):
        assert '"give fuel" as giving fuel' in story_source

    def test_check_requires_prep_begun(self, story_source):
        check_idx = story_source.find("Check giving fuel:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 300]
        assert "selengrad-prep-begun is false" in block

    def test_check_blocks_after_choice(self, story_source):
        check_idx = story_source.find("Check giving fuel:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 300]
        assert "fuel-choice-made is true" in block

    def test_carry_out_sets_martyr(self, story_source):
        carry_idx = story_source.find("Carry out giving fuel:")
        assert carry_idx != -1
        block = story_source[carry_idx:carry_idx + 200]
        assert "now chose-martyr is true" in block

    def test_carry_out_sets_choice_made(self, story_source):
        carry_idx = story_source.find("Carry out giving fuel:")
        assert carry_idx != -1
        block = story_source[carry_idx:carry_idx + 200]
        assert "now fuel-choice-made is true" in block

    def test_report_has_placeholder(self, story_source):
        report_idx = story_source.find("Report giving fuel:")
        assert report_idx != -1
        block = story_source[report_idx:report_idx + 400]
        assert "TODO prose: #55" in block


# ── E1 / E2 Dispatch ────────────────────────────────────────────────


class TestE1E2Dispatch:
    """The every-turn dispatch rule advances D1-counter and fires endings."""

    def test_dispatch_rule_exists(self, story_source):
        """An every-turn rule fires when fuel-choice-made is true."""
        assert "Every turn when fuel-choice-made is true" in story_source

    def test_counter_increments(self, story_source):
        """D1-counter increments each turn after fuel choice."""
        idx = story_source.find("Every turn when fuel-choice-made is true")
        assert idx != -1
        block = story_source[idx:idx + 800]
        assert "increase D1-counter by 1" in block

    def test_e1_ending_on_split(self, story_source):
        """E1 fires when counter threshold met and split was chosen."""
        idx = story_source.find("Every turn when fuel-choice-made is true")
        assert idx != -1
        block = story_source[idx:idx + 800]
        assert "chose-split-fuel is true" in block
        assert "reached Selengrad" in block or "Selengrad" in block

    def test_e2_ending_on_martyr(self, story_source):
        """E2 fires when counter threshold met and martyr was chosen."""
        idx = story_source.find("Every turn when fuel-choice-made is true")
        assert idx != -1
        block = story_source[idx:idx + 1200]
        assert "chose-martyr is true" in block
        assert "gave them the Moon" in block or "Martyr" in block

    def test_e1_has_placeholder(self, story_source):
        """E1 ending text is tagged as placeholder."""
        idx = story_source.find("reached Selengrad")
        assert idx != -1
        block = story_source[max(0, idx - 500):idx]
        assert "TODO prose: #55" in block

    def test_e2_has_placeholder(self, story_source):
        """E2 ending text is tagged as placeholder."""
        idx = story_source.find("gave them the Moon")
        assert idx != -1
        block = story_source[max(0, idx - 500):idx]
        assert "TODO prose: #55" in block

    def test_e1_ends_story(self, story_source):
        """E1 path calls 'end the story'."""
        idx = story_source.find("You have reached Selengrad")
        assert idx != -1
        block = story_source[max(0, idx - 100):idx + 100]
        assert "end the story" in block

    def test_e2_ends_story(self, story_source):
        """E2 path calls 'end the story'."""
        idx = story_source.find("You gave them the Moon")
        assert idx != -1
        block = story_source[max(0, idx - 100):idx + 100]
        assert "end the story" in block


# ── Mutual Exclusivity ───────────────────────────────────────────────


class TestMutualExclusivity:
    """Only one fuel choice can be made; the other is blocked afterwards."""

    def test_split_blocks_after_choice(self, story_source):
        """Split fuel check blocks if fuel-choice-made is true."""
        check_idx = story_source.find("Check splitting fuel:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 300]
        assert "fuel-choice-made is true" in block

    def test_give_blocks_after_choice(self, story_source):
        """Give fuel check blocks if fuel-choice-made is true."""
        check_idx = story_source.find("Check giving fuel:")
        assert check_idx != -1
        block = story_source[check_idx:check_idx + 300]
        assert "fuel-choice-made is true" in block


# ── Test Scripts ─────────────────────────────────────────────────────


class TestWalkthroughScripts:
    """Test scripts cover the full E1 and E2 paths."""

    def test_e1_test_script_exists(self, story_source):
        assert "Test selengrad-e1 with" in story_source

    def test_e2_test_script_exists(self, story_source):
        assert "Test selengrad-e2 with" in story_source

    def test_e1_script_includes_transmit(self, story_source):
        idx = story_source.find("Test selengrad-e1 with")
        assert idx != -1
        script = story_source[idx:story_source.find("\n", idx + 1)]
        assert "transmit" in script.lower()

    def test_e1_script_includes_prepare(self, story_source):
        idx = story_source.find("Test selengrad-e1 with")
        assert idx != -1
        script = story_source[idx:story_source.find("\n", idx + 1)]
        assert "prepare selengrad" in script.lower()

    def test_e1_script_includes_split(self, story_source):
        idx = story_source.find("Test selengrad-e1 with")
        assert idx != -1
        script = story_source[idx:story_source.find("\n", idx + 1)]
        assert "split fuel" in script.lower()

    def test_e2_script_includes_give(self, story_source):
        idx = story_source.find("Test selengrad-e2 with")
        assert idx != -1
        script = story_source[idx:story_source.find("\n", idx + 1)]
        assert "give fuel" in script.lower()


# ── Placeholder Prose ────────────────────────────────────────────────


class TestPlaceholderProse:
    """All new prose is clearly tagged with [TODO prose: #55]."""

    def test_all_new_sections_have_placeholders(self, story_source):
        """Each of the new report/say blocks contains the TODO tag."""
        # Find the Selengrad arc part
        arc_start = story_source.find("Part 8B - Selengrad Arc")
        assert arc_start != -1, "Selengrad arc Part not found"
        arc_block = story_source[arc_start:]
        # Cut at the next Part
        next_part = arc_block.find("\nPart 9")
        if next_part != -1:
            arc_block = arc_block[:next_part]
        # Count TODO tags — should be at least 4 (D1 report, split report,
        # give report, E1 say, E2 say)
        todo_count = arc_block.count("TODO prose: #55")
        assert todo_count >= 4, (
            f"Expected >= 4 placeholder tags in Selengrad arc, found {todo_count}"
        )
