"""Tests for mirs_end_bridge.logs."""

import json
from pathlib import Path

import pytest

from mirs_end_bridge.logs import log_call, set_log_dir
from mirs_end_bridge.types import Prompt


@pytest.fixture(autouse=True)
def _use_tmp_log_dir(tmp_path):
    """Redirect log output to a temp directory for testing."""
    log_dir = tmp_path / "logs" / "llm-calls"
    set_log_dir(log_dir)
    yield log_dir
    set_log_dir(None)


def _make_prompt() -> Prompt:
    return Prompt(
        system="Test system prompt",
        messages=[{"role": "user", "content": "Hello"}],
    )


class TestLogCall:
    def test_creates_log_file(self, _use_tmp_log_dir):
        log_dir = _use_tmp_log_dir
        log_file = log_call(
            role="station-ai",
            prompt=_make_prompt(),
            response_text="Comrade.",
            input_tokens=100,
            output_tokens=25,
            cost_usd=0.000675,
            model="claude-sonnet-4-5",
        )
        assert log_file.exists()
        assert log_file.suffix == ".jsonl"

    def test_entry_shape(self, _use_tmp_log_dir):
        log_file = log_call(
            role="narrator",
            prompt=_make_prompt(),
            response_text="The corridor stretches ahead.",
            input_tokens=200,
            output_tokens=50,
            cost_usd=0.001,
            model="claude-sonnet-4-5",
        )
        with open(log_file) as f:
            entry = json.loads(f.readline())

        assert entry["role"] == "narrator"
        assert entry["model"] == "claude-sonnet-4-5"
        assert entry["input_tokens"] == 200
        assert entry["output_tokens"] == 50
        assert entry["cost_usd"] == 0.001
        assert "timestamp" in entry
        assert entry["response_text"] == "The corridor stretches ahead."

    def test_append_only(self, _use_tmp_log_dir):
        prompt = _make_prompt()
        log_call(
            role="station-ai",
            prompt=prompt,
            response_text="First.",
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.0001,
            model="claude-sonnet-4-5",
        )
        log_file = log_call(
            role="station-ai",
            prompt=prompt,
            response_text="Second.",
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.0001,
            model="claude-sonnet-4-5",
        )
        with open(log_file) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_system_preview_truncated(self, _use_tmp_log_dir):
        long_system = "A" * 500
        prompt = Prompt(
            system=long_system,
            messages=[{"role": "user", "content": "Hi"}],
        )
        log_file = log_call(
            role="test",
            prompt=prompt,
            response_text="Ok.",
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.0001,
            model="claude-sonnet-4-5",
        )
        with open(log_file) as f:
            entry = json.loads(f.readline())
        assert len(entry["prompt_system_preview"]) == 200
        assert entry["prompt_system_length"] == 500
