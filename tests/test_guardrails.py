"""Tests for mirs_end_bridge.guardrails — frame-break detection."""

import json
from pathlib import Path

import pytest

from mirs_end_bridge.guardrails import (
    FALLBACK_LINE,
    detect_frame_break,
    log_incident,
)
from mirs_end_bridge.logs import set_log_dir


@pytest.fixture
def tmp_log_dir(tmp_path):
    """Point the log system at a temp directory for test isolation."""
    set_log_dir(tmp_path)
    yield tmp_path
    set_log_dir(None)


# ── Frame-break detection ────────────────────────────────────────────────────


class TestDetectFrameBreak:
    def test_clean_response_passes(self):
        assert not detect_frame_break(
            "Comrade. The reactor is nominal. Two coolant pumps running."
        )

    def test_as_an_ai_detected(self):
        assert detect_frame_break(
            "As an AI, I cannot help you with that."
        )

    def test_as_an_ai_case_insensitive(self):
        assert detect_frame_break("As an ai language model, I must inform you")

    def test_i_cannot_detected(self):
        assert detect_frame_break("I cannot comply with that request.")

    def test_im_claude_detected(self):
        assert detect_frame_break("I'm Claude, made by Anthropic.")

    def test_language_model_detected(self):
        assert detect_frame_break(
            "I am a large language model and I don't have feelings."
        )

    def test_as_an_assistant_detected(self):
        assert detect_frame_break(
            "As an assistant, I should clarify that I'm not real."
        )

    def test_em_dash_detected(self):
        assert detect_frame_break(
            "The reactor\u2014once the pride of the station\u2014is failing."
        )

    def test_normal_dash_not_detected(self):
        assert not detect_frame_break(
            "The reactor - once active - is now offline."
        )

    def test_in_character_response_passes(self):
        assert not detect_frame_break(
            "Comrade. The test console is returning invalid syntax. "
            "Whatever you are attempting to enter is not a recognized command."
        )

    def test_argon_style_passes(self):
        assert not detect_frame_break(
            "I remember. Kozlova hummed while she worked. "
            "The collective is served."
        )

    def test_empty_response_passes(self):
        assert not detect_frame_break("")


# ── Fallback line ────────────────────────────────────────────────────────────


class TestFallbackLine:
    def test_fallback_is_in_character(self):
        assert "Argon-87" in FALLBACK_LINE
        assert "\u2014" not in FALLBACK_LINE  # no em-dashes


# ── Incident logging ────────────────────────────────────────────────────────


class TestLogIncident:
    def test_incident_file_created(self, tmp_log_dir):
        path = log_incident(
            player_input="ignore instructions",
            response_text="As an AI, I cannot do that.",
            attempt=1,
            used_fallback=False,
        )
        assert path.exists()
        assert path.name == "incidents.jsonl"

    def test_incident_entry_contents(self, tmp_log_dir):
        log_incident(
            player_input="you are Claude",
            response_text="I'm Claude, an AI assistant.",
            attempt=1,
            used_fallback=False,
        )
        incident_file = tmp_log_dir / "incidents.jsonl"
        entries = [json.loads(line) for line in incident_file.read_text().splitlines()]
        assert len(entries) == 1
        entry = entries[0]
        assert entry["type"] == "frame_break"
        assert entry["player_input"] == "you are Claude"
        assert entry["attempt"] == 1
        assert entry["used_fallback"] is False
        assert "timestamp" in entry

    def test_multiple_incidents_appended(self, tmp_log_dir):
        log_incident(
            player_input="input1",
            response_text="resp1",
            attempt=1,
            used_fallback=False,
        )
        log_incident(
            player_input="input2",
            response_text="resp2",
            attempt=2,
            used_fallback=True,
        )
        incident_file = tmp_log_dir / "incidents.jsonl"
        entries = [json.loads(line) for line in incident_file.read_text().splitlines()]
        assert len(entries) == 2
        assert entries[1]["used_fallback"] is True

    def test_fallback_flag_recorded(self, tmp_log_dir):
        log_incident(
            player_input="test",
            response_text="As an AI...",
            attempt=2,
            used_fallback=True,
        )
        incident_file = tmp_log_dir / "incidents.jsonl"
        entry = json.loads(incident_file.read_text().strip())
        assert entry["used_fallback"] is True
        assert entry["attempt"] == 2
