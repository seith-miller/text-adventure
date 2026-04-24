"""Claude API wrapper for Mir's End.

Provides a single ``call_claude`` function with retry logic, cost accounting,
and structured error handling. All Claude calls in the project go through here.
"""

from __future__ import annotations

import os
import time
from typing import Any

import anthropic

from .logs import log_call
from .types import CostReport, LLMResponse, Prompt

# ── Cost tables (USD per token, as of 2025) ─────────────────────────────────

_COST_PER_INPUT_TOKEN: dict[str, float] = {
    "claude-sonnet-4-5": 3.0 / 1_000_000,
    "claude-sonnet-4-5-20250514": 3.0 / 1_000_000,
    "claude-haiku-3-5": 0.80 / 1_000_000,
    "claude-haiku-3-5-20241022": 0.80 / 1_000_000,
}
_COST_PER_OUTPUT_TOKEN: dict[str, float] = {
    "claude-sonnet-4-5": 15.0 / 1_000_000,
    "claude-sonnet-4-5-20250514": 15.0 / 1_000_000,
    "claude-haiku-3-5": 4.0 / 1_000_000,
    "claude-haiku-3-5-20241022": 4.0 / 1_000_000,
}

# Fallback for unknown models.
_DEFAULT_INPUT_COST = 3.0 / 1_000_000
_DEFAULT_OUTPUT_COST = 15.0 / 1_000_000

# ── Retry configuration ─────────────────────────────────────────────────────

_MAX_RETRIES = 3
_INITIAL_BACKOFF_S = 1.0

# ── Session-level cost accumulator ──────────────────────────────────────────

_cost_report = CostReport()


class BridgeAPIError(Exception):
    """Raised when a Claude API call fails after all retries."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class MissingAPIKeyError(BridgeAPIError):
    """Raised when ANTHROPIC_API_KEY is not set."""

    def __init__(self) -> None:
        super().__init__(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Set it before calling the bridge.",
            status_code=None,
        )


def _estimate_cost(
    model: str, input_tokens: int, output_tokens: int
) -> float:
    input_rate = _COST_PER_INPUT_TOKEN.get(model, _DEFAULT_INPUT_COST)
    output_rate = _COST_PER_OUTPUT_TOKEN.get(model, _DEFAULT_OUTPUT_COST)
    return input_tokens * input_rate + output_tokens * output_rate


def call_claude(
    prompt: Prompt,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 1024,
    *,
    _client: Any | None = None,
) -> LLMResponse:
    """Send *prompt* to Claude and return an ``LLMResponse``.

    Parameters
    ----------
    prompt:
        A Prompt dict with ``system`` and ``messages`` keys.
    model:
        Anthropic model identifier.
    max_tokens:
        Maximum tokens in the response.
    _client:
        Optional pre-built Anthropic client (used for testing).

    Raises
    ------
    MissingAPIKeyError
        If ``ANTHROPIC_API_KEY`` is not set and no *_client* is provided.
    BridgeAPIError
        If the API call fails after retries.
    """
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise MissingAPIKeyError()
        client = anthropic.Anthropic(api_key=api_key)
    else:
        client = _client

    last_error: Exception | None = None
    backoff = _INITIAL_BACKOFF_S

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=prompt["system"],
                messages=prompt["messages"],
            )

            text = response.content[0].text if response.content else ""
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = _estimate_cost(model, input_tokens, output_tokens)

            result = LLMResponse(
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
            )

            # Accumulate cost report.
            _cost_report.total_calls += 1
            _cost_report.total_input_tokens += input_tokens
            _cost_report.total_output_tokens += output_tokens
            _cost_report.total_cost_usd += cost
            _cost_report.calls.append({
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost,
            })

            # Log the call.
            log_call(
                role="unknown",
                prompt=prompt,
                response_text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                model=model,
            )

            return result

        except anthropic.RateLimitError as exc:
            last_error = exc
            time.sleep(backoff)
            backoff *= 2

        except anthropic.APIError as exc:
            raise BridgeAPIError(
                str(exc),
                status_code=getattr(exc, "status_code", None),
            ) from exc

    raise BridgeAPIError(
        f"Rate limited after {_MAX_RETRIES} retries",
        status_code=429,
    ) from last_error


def get_cost_report() -> CostReport:
    """Return the cumulative cost report for this session."""
    return _cost_report


def reset_cost_report() -> None:
    """Reset the cost accumulator (useful for testing)."""
    global _cost_report
    _cost_report = CostReport()
