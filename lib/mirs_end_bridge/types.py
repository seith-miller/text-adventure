"""Type definitions for the Mir's End LLM bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict


class ResourcesDict(TypedDict):
    o2: int
    morale: int
    dose: int | None


class GameState(TypedDict):
    currentRoom: str
    inventory: list[str]
    truthStates: dict[str, bool]
    resources: ResourcesDict
    score: int
    turn: int
    recentTranscript: str
    shipState: dict


class Prompt(TypedDict):
    system: str
    messages: list[dict[str, str]]


@dataclass
class LLMResponse:
    """Response from a Claude API call."""

    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass
class CostReport:
    """Cumulative cost report for all Claude calls in this session."""

    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    calls: list[dict] = field(default_factory=list)
