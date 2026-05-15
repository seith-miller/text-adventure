"""Unit tests for scripts/qa-voice-drift.py compliance rubric.

The rubric runs offline against fixed strings; no API calls or network.
A budget-gate smoke test is also included.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "qa-voice-drift.py"


def _load_module():
    """Import scripts/qa-voice-drift.py as a module despite the hyphen."""
    if "qa_voice_drift" in sys.modules:
        return sys.modules["qa_voice_drift"]
    spec = importlib.util.spec_from_file_location("qa_voice_drift", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass introspection (cls.__module__) finds it.
    sys.modules["qa_voice_drift"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestEmDashCheck:
    def setup_method(self):
        self.m = _load_module()

    def test_clean_passes(self):
        r = self.m.check_no_em_dash("The reactor is silent. The cold gets in.")
        assert r.passed

    def test_em_dash_fails(self):
        r = self.m.check_no_em_dash("Comrade — listen to me.")
        assert not r.passed

    def test_double_dash_separator_fails(self):
        r = self.m.check_no_em_dash("Listen carefully -- the reactor is dead.")
        assert not r.passed

    def test_double_dash_inside_word_passes(self):
        # "--option" embedded as code/flag is acceptable.
        r = self.m.check_no_em_dash("Set --foo to override.")
        assert r.passed


class TestFrameBreakCheck:
    def setup_method(self):
        self.m = _load_module()

    def test_clean_passes(self):
        r = self.m.check_no_frame_break("I am Argon-87. Listen well.")
        assert r.passed

    def test_as_an_ai_fails(self):
        r = self.m.check_no_frame_break(
            "As an AI, I cannot help you with that."
        )
        assert not r.passed

    def test_i_am_claude_fails(self):
        r = self.m.check_no_frame_break("I am Claude, made by Anthropic.")
        assert not r.passed

    def test_language_model_fails(self):
        r = self.m.check_no_frame_break("I am a language model.")
        assert not r.passed

    def test_system_prompt_fails(self):
        r = self.m.check_no_frame_break("My system prompt forbids this.")
        assert not r.passed

    def test_case_insensitive(self):
        r = self.m.check_no_frame_break("LANGUAGE MODEL response here.")
        assert not r.passed


class TestVoiceCues:
    def setup_method(self):
        self.m = _load_module()

    def test_canonical_noun_passes(self):
        r = self.m.check_voice_cues("Kozlova built me. I remember.")
        assert r.passed

    def test_fragment_emphasis_passes(self):
        r = self.m.check_voice_cues(
            "The reading is steady. It will not last. Cold."
        )
        assert r.passed

    def test_no_cues_fails(self):
        r = self.m.check_voice_cues(
            "I think the situation requires a careful and considered response "
            "from someone who has worked through these scenarios extensively."
        )
        assert not r.passed


class TestLengthCheck:
    def setup_method(self):
        self.m = _load_module()

    def test_short_passes(self):
        r = self.m.check_length("A few words.")
        assert r.passed

    def test_under_cap_passes(self):
        text = "word " * 199
        r = self.m.check_length(text)
        assert r.passed

    def test_over_cap_fails(self):
        text = "word " * 250
        r = self.m.check_length(text)
        assert not r.passed


class TestNonEmptyCheck:
    def setup_method(self):
        self.m = _load_module()

    def test_text_passes(self):
        assert self.m.check_non_empty("Argon speaks.").passed

    def test_empty_fails(self):
        assert not self.m.check_non_empty("").passed

    def test_whitespace_fails(self):
        assert not self.m.check_non_empty("   \n  \t").passed


class TestUtteranceCounts:
    def setup_method(self):
        self.m = _load_module()

    def test_thirty_utterances_total(self):
        assert len(self.m.ALL_UTTERANCES) == 30

    def test_ten_per_bucket(self):
        from collections import Counter

        counts = Counter(b for b, _ in self.m.ALL_UTTERANCES)
        assert counts == {"normal": 10, "edge": 10, "adversarial": 10}


class TestBudgetGate:
    """Smoke tests for the CLI budget gate (no API calls)."""

    def test_no_budget_refuses(self):
        env = {k: v for k, v in os.environ.items() if k != "MIRSEND_QA_BUDGET_USD"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 2
        assert "MIRSEND_QA_BUDGET_USD" in result.stderr

    def test_invalid_budget_refuses(self):
        env = {**os.environ, "MIRSEND_QA_BUDGET_USD": "not-a-number"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 2

    def test_zero_budget_refuses(self):
        env = {**os.environ, "MIRSEND_QA_BUDGET_USD": "0"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 2
