"""Tests for mirs_end_bridge.claude.

All Claude API calls are mocked; no real API key or network access needed.
"""

import os
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from mirs_end_bridge.claude import (
    BridgeAPIError,
    MissingAPIKeyError,
    call_claude,
    get_cost_report,
    reset_cost_report,
)
from mirs_end_bridge.logs import set_log_dir
from mirs_end_bridge.types import Prompt


@pytest.fixture(autouse=True)
def _reset_costs(tmp_path):
    """Reset cost report and redirect logs for each test."""
    reset_cost_report()
    set_log_dir(tmp_path / "logs")
    yield
    set_log_dir(None)


def _make_prompt() -> Prompt:
    return Prompt(
        system="You are a test.",
        messages=[{"role": "user", "content": "Hello"}],
    )


def _mock_response(text="Hello back", input_tokens=50, output_tokens=20):
    """Build a mock Anthropic response object."""
    content_block = MagicMock()
    content_block.text = text

    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens

    response = MagicMock()
    response.content = [content_block]
    response.usage = usage
    return response


class TestCallClaude:
    def test_basic_call(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response()

        result = call_claude(_make_prompt(), _client=client)
        assert result.text == "Hello back"
        assert result.input_tokens == 50
        assert result.output_tokens == 20
        assert result.cost_usd > 0

    def test_cost_accumulation(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response()

        call_claude(_make_prompt(), _client=client)
        call_claude(_make_prompt(), _client=client)

        report = get_cost_report()
        assert report.total_calls == 2
        assert report.total_input_tokens == 100
        assert report.total_output_tokens == 40
        assert report.total_cost_usd > 0

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove key if present
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(MissingAPIKeyError):
                call_claude(_make_prompt())

    def test_retry_on_rate_limit(self):
        import anthropic as anthropic_module

        client = MagicMock()
        # Fail twice with 429, then succeed.
        mock_response = MagicMock(status_code=429, headers={})
        mock_response.request = MagicMock()
        rate_err = anthropic_module.RateLimitError(
            message="Rate limited",
            response=mock_response,
            body=None,
        )
        client.messages.create.side_effect = [
            rate_err,
            rate_err,
            _mock_response(),
        ]

        with patch("mirs_end_bridge.claude.time.sleep"):
            result = call_claude(_make_prompt(), _client=client)

        assert result.text == "Hello back"
        assert client.messages.create.call_count == 3

    def test_rate_limit_exhausted(self):
        import anthropic as anthropic_module

        client = MagicMock()
        mock_response = MagicMock(status_code=429, headers={})
        mock_response.request = MagicMock()
        rate_err = anthropic_module.RateLimitError(
            message="Rate limited",
            response=mock_response,
            body=None,
        )
        client.messages.create.side_effect = rate_err

        with patch("mirs_end_bridge.claude.time.sleep"):
            with pytest.raises(BridgeAPIError, match="Rate limited"):
                call_claude(_make_prompt(), _client=client)

    def test_api_error_raises_bridge_error(self):
        import anthropic as anthropic_module

        client = MagicMock()
        client.messages.create.side_effect = anthropic_module.APIError(
            message="Server error",
            request=MagicMock(),
            body=None,
        )

        with pytest.raises(BridgeAPIError):
            call_claude(_make_prompt(), _client=client)


class TestCostReport:
    def test_reset(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response()
        call_claude(_make_prompt(), _client=client)

        reset_cost_report()
        report = get_cost_report()
        assert report.total_calls == 0
        assert report.total_cost_usd == 0.0
