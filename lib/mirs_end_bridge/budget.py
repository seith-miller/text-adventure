"""Cost-cap enforcement for Mir's End AI features.

Three independent caps protect against runaway spend:

1. **Per-call cap** — rejects a single call whose estimated cost exceeds the
   limit *before* the API is invoked.
2. **Per-session cap** — tracks cumulative spend for one playthrough and blocks
   further calls once the cap is reached.
3. **Per-day cap** — tracks cumulative spend across all sessions in a rolling
   24-hour window and blocks new calls once the cap is reached.

Configuration is loaded from ``config/ai.toml`` (TOML) and can be overridden
by environment variables ``MIRSEND_CAP_PER_CALL``, ``MIRSEND_CAP_PER_SESSION``,
and ``MIRSEND_CAP_PER_DAY``.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from .spend_log import SpendLog

# ── Project paths ────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "config" / "ai.toml"

# ── Defaults (match config/ai.toml) ─────────────────────────────────────────

_DEFAULT_PER_CALL = 0.02
_DEFAULT_PER_SESSION = 0.25
_DEFAULT_PER_DAY = 5.00

# ── Typed errors ─────────────────────────────────────────────────────────────


class BudgetError(Exception):
    """Base class for budget-related rejections."""


class PerCallCapExceeded(BudgetError):
    """Raised when a single call's estimated cost exceeds the per-call cap."""

    def __init__(self, estimated: float, cap: float) -> None:
        self.estimated = estimated
        self.cap = cap
        super().__init__(
            f"Estimated call cost ${estimated:.4f} exceeds per-call cap ${cap:.4f}"
        )


class PerSessionCapExceeded(BudgetError):
    """Raised when the cumulative session spend has reached the per-session cap."""

    def __init__(self, session_spend: float, cap: float) -> None:
        self.session_spend = session_spend
        self.cap = cap
        super().__init__(
            f"Session spend ${session_spend:.4f} has reached per-session cap ${cap:.4f}"
        )


class PerDayCapExceeded(BudgetError):
    """Raised when the rolling 24-hour spend has reached the per-day cap."""

    def __init__(self, day_spend: float, cap: float) -> None:
        self.day_spend = day_spend
        self.cap = cap
        super().__init__(
            f"24-hour spend ${day_spend:.4f} has reached per-day cap ${cap:.4f}"
        )


# ── Configuration loader ────────────────────────────────────────────────────


def load_caps(config_path: Path | None = None) -> dict[str, float]:
    """Load cap values from TOML config, with env-var overrides.

    Returns a dict with keys ``per_call``, ``per_session``, ``per_day``.
    """
    caps = {
        "per_call": _DEFAULT_PER_CALL,
        "per_session": _DEFAULT_PER_SESSION,
        "per_day": _DEFAULT_PER_DAY,
    }

    path = config_path or _DEFAULT_CONFIG_PATH
    if path.exists():
        with open(path, "rb") as f:
            data = tomllib.load(f)
        toml_caps = data.get("caps", {})
        for key in caps:
            if key in toml_caps:
                caps[key] = float(toml_caps[key])

    # Env-var overrides take precedence.
    env_map = {
        "MIRSEND_CAP_PER_CALL": "per_call",
        "MIRSEND_CAP_PER_SESSION": "per_session",
        "MIRSEND_CAP_PER_DAY": "per_day",
    }
    for env_var, key in env_map.items():
        val = os.environ.get(env_var)
        if val is not None:
            caps[key] = float(val)

    return caps


# ── Budget tracker ───────────────────────────────────────────────────────────


class BudgetTracker:
    """Thread-safe budget enforcement for a single session.

    Instantiate one per session.  Call :meth:`check_budget` before every
    Claude call and :meth:`record_spend` after a successful call.

    Parameters
    ----------
    session_id:
        Unique identifier for this playthrough.
    caps:
        Dict with ``per_call``, ``per_session``, ``per_day`` float values.
        Defaults to :func:`load_caps()`.
    spend_log:
        A :class:`SpendLog` instance for persisting and querying spend data.
        Defaults to a new instance with the default log path.
    """

    # In-fiction canned line when the per-session cap is hit.
    DEGRADED_MESSAGE = (
        "Argon-87's voice cuts out. Power rationing protocol."
    )

    # One-time first-contact notice shown before the first AI interaction.
    FIRST_CONTACT_TEMPLATE = (
        "Argon-87 is an LLM-driven character. Interactions use your "
        "Anthropic API credits. Budget cap for this session: ${cap:.2f}. "
        "See docs/ai-setup.md."
    )

    def __init__(
        self,
        session_id: str,
        caps: dict[str, float] | None = None,
        spend_log: SpendLog | None = None,
    ) -> None:
        self.session_id = session_id
        self.caps = caps or load_caps()
        self.spend_log = spend_log or SpendLog()

        self._lock = threading.Lock()
        self._session_spend: float = 0.0
        self._session_calls: int = 0
        self._degraded: bool = False
        self._degraded_message_shown: bool = False
        self._first_contact_shown: bool = False

    # ── Public query properties ──────────────────────────────────────────

    @property
    def session_spend(self) -> float:
        with self._lock:
            return self._session_spend

    @property
    def session_calls(self) -> int:
        with self._lock:
            return self._session_calls

    @property
    def is_degraded(self) -> bool:
        with self._lock:
            return self._degraded

    # ── First-contact notice ─────────────────────────────────────────────

    def get_first_contact_notice(self) -> str | None:
        """Return the first-contact notice, or ``None`` if already shown."""
        with self._lock:
            if self._first_contact_shown:
                return None
            self._first_contact_shown = True
            return self.FIRST_CONTACT_TEMPLATE.format(
                cap=self.caps["per_session"]
            )

    # ── Pre-call check ───────────────────────────────────────────────────

    def check_budget(self, estimated_cost: float) -> None:
        """Raise a :class:`BudgetError` if the call should be rejected.

        Must be called *before* the API call is made.

        Parameters
        ----------
        estimated_cost:
            Pre-estimated cost of the call (e.g. from token count heuristic).

        Raises
        ------
        PerCallCapExceeded
            If ``estimated_cost`` exceeds the per-call cap.
        PerSessionCapExceeded
            If the session has already exhausted its budget.
        PerDayCapExceeded
            If the rolling 24-hour window has exhausted the daily budget.
        """
        with self._lock:
            # Already in degraded mode — reject silently.
            if self._degraded:
                raise PerSessionCapExceeded(
                    self._session_spend, self.caps["per_session"]
                )

            # Per-call cap.
            if estimated_cost > self.caps["per_call"]:
                raise PerCallCapExceeded(estimated_cost, self.caps["per_call"])

            # Per-session cap.
            if self._session_spend >= self.caps["per_session"]:
                self._degraded = True
                raise PerSessionCapExceeded(
                    self._session_spend, self.caps["per_session"]
                )

            # Per-day cap (reads from persistent log).
            day_spend = self.spend_log.rolling_24h_spend()
            if day_spend >= self.caps["per_day"]:
                raise PerDayCapExceeded(day_spend, self.caps["per_day"])

    # ── Post-call recording ──────────────────────────────────────────────

    def record_spend(
        self,
        *,
        role: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        model: str = "",
    ) -> None:
        """Record a completed call's cost atomically.

        Persists the entry to the spend log and updates session counters.
        If the session cap is now exceeded, enters degraded mode.
        """
        with self._lock:
            self._session_spend += cost_usd
            self._session_calls += 1

            self.spend_log.append(
                session_id=self.session_id,
                role=role,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                model=model,
            )

            if self._session_spend >= self.caps["per_session"]:
                self._degraded = True

    # ── Degraded-mode message ────────────────────────────────────────────

    def get_degraded_message(self) -> str | None:
        """Return the canned degraded-mode line once, then ``None``."""
        with self._lock:
            if self._degraded and not self._degraded_message_shown:
                self._degraded_message_shown = True
                return self.DEGRADED_MESSAGE
            return None

    # ── Day-cap pre-check (for disabling AI at session start) ────────────

    def is_day_cap_exceeded(self) -> bool:
        """Check whether the 24-hour rolling cap is already exceeded.

        Used at session start to pre-disable AI features.
        """
        return self.spend_log.rolling_24h_spend() >= self.caps["per_day"]

    def get_day_cap_message(self) -> str | None:
        """Return a setup message if the daily cap is already hit."""
        if self.is_day_cap_exceeded():
            return (
                "AI features are currently disabled. The daily spending "
                f"cap of ${self.caps['per_day']:.2f} has been reached. "
                "Features will re-enable as older spend ages out of the "
                "24-hour window."
            )
        return None
