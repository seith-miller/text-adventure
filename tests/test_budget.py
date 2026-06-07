"""Tests for Mir's End cost-cap and budget enforcement.

Covers:
- Per-call cap rejection
- Per-session cap enforcement and degraded mode
- Per-day (rolling 24h) cap enforcement
- Spend log persistence and querying
- Config loading from TOML and env vars
- Degraded-mode canned line fires once
- First-contact notice fires once
- No API call fires after any cap is reached
- Report script basic functionality
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure lib/ is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from mirs_end_bridge.budget import (
    BudgetError,
    BudgetTracker,
    PerCallCapExceeded,
    PerDayCapExceeded,
    PerSessionCapExceeded,
    load_caps,
)
from mirs_end_bridge.spend_log import SpendLog


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_log(tmp_path: Path) -> SpendLog:
    """A SpendLog writing to a temp file."""
    return SpendLog(log_path=tmp_path / "test-spend.jsonl")


@pytest.fixture
def tracker(tmp_log: SpendLog) -> BudgetTracker:
    """A BudgetTracker with default caps and a temp spend log."""
    caps = {"per_call": 0.02, "per_session": 0.25, "per_day": 5.00}
    return BudgetTracker(session_id="test-session", caps=caps, spend_log=tmp_log)


@pytest.fixture
def tight_tracker(tmp_log: SpendLog) -> BudgetTracker:
    """A BudgetTracker with very tight caps for testing boundaries."""
    caps = {"per_call": 0.01, "per_session": 0.03, "per_day": 0.10}
    return BudgetTracker(session_id="tight-session", caps=caps, spend_log=tmp_log)


# ── Per-call cap tests ──────────────────────────────────────────────────────


class TestPerCallCap:
    def test_call_under_cap_passes(self, tracker: BudgetTracker) -> None:
        """A call estimated below the per-call cap should not raise."""
        tracker.check_budget(estimated_cost=0.01)

    def test_call_at_cap_passes(self, tracker: BudgetTracker) -> None:
        """A call exactly at the per-call cap should pass."""
        tracker.check_budget(estimated_cost=0.02)

    def test_call_over_cap_rejected(self, tracker: BudgetTracker) -> None:
        """A call estimated above the per-call cap should raise."""
        with pytest.raises(PerCallCapExceeded) as exc_info:
            tracker.check_budget(estimated_cost=0.03)
        assert exc_info.value.estimated == 0.03
        assert exc_info.value.cap == 0.02

    def test_per_call_is_budget_error(self, tracker: BudgetTracker) -> None:
        """PerCallCapExceeded should be a subclass of BudgetError."""
        with pytest.raises(BudgetError):
            tracker.check_budget(estimated_cost=0.05)

    def test_pathological_request_blocked(self, tracker: BudgetTracker) -> None:
        """A very expensive estimated call should be rejected."""
        with pytest.raises(PerCallCapExceeded):
            tracker.check_budget(estimated_cost=1.00)


# ── Per-session cap tests ───────────────────────────────────────────────────


class TestPerSessionCap:
    def test_spend_under_cap(self, tracker: BudgetTracker) -> None:
        """Calls within the session cap should succeed."""
        for _ in range(10):
            tracker.check_budget(estimated_cost=0.01)
            tracker.record_spend(
                role="station-ai",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )
        # Total: $0.10, cap is $0.25 — should be fine.
        assert tracker.session_spend == pytest.approx(0.10)
        assert not tracker.is_degraded

    def test_session_cap_triggers_degraded_mode(
        self, tight_tracker: BudgetTracker
    ) -> None:
        """Once session spend reaches the cap, tracker enters degraded mode."""
        # Cap is $0.03.  Three calls at $0.01 each = $0.03.
        for _ in range(3):
            tight_tracker.check_budget(estimated_cost=0.01)
            tight_tracker.record_spend(
                role="station-ai",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )
        assert tight_tracker.is_degraded
        assert tight_tracker.session_spend == pytest.approx(0.03)

    def test_calls_blocked_after_session_cap(
        self, tight_tracker: BudgetTracker
    ) -> None:
        """No further calls should fire once the session cap is hit."""
        for _ in range(3):
            tight_tracker.check_budget(estimated_cost=0.01)
            tight_tracker.record_spend(
                role="station-ai",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )
        with pytest.raises(PerSessionCapExceeded):
            tight_tracker.check_budget(estimated_cost=0.005)

    def test_degraded_message_fires_once(
        self, tight_tracker: BudgetTracker
    ) -> None:
        """The canned degraded line should fire exactly once."""
        for _ in range(3):
            tight_tracker.check_budget(estimated_cost=0.01)
            tight_tracker.record_spend(
                role="station-ai",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )
        msg = tight_tracker.get_degraded_message()
        assert msg == BudgetTracker.DEGRADED_MESSAGE

        # Second call returns None.
        assert tight_tracker.get_degraded_message() is None

    def test_session_spend_is_atomic(self, tmp_log: SpendLog) -> None:
        """Multiple record_spend calls update the counter correctly."""
        caps = {"per_call": 1.0, "per_session": 1.0, "per_day": 10.0}
        t = BudgetTracker(session_id="atomic-test", caps=caps, spend_log=tmp_log)

        for i in range(5):
            t.record_spend(
                role="test",
                input_tokens=10,
                output_tokens=5,
                cost_usd=0.1,
            )
        assert t.session_spend == pytest.approx(0.5)
        assert t.session_calls == 5


# ── Per-day cap tests ───────────────────────────────────────────────────────


class TestPerDayCap:
    def test_day_cap_blocks_call(self, tmp_path: Path) -> None:
        """Once the 24h spend exceeds the daily cap, calls are rejected."""
        log = SpendLog(log_path=tmp_path / "day-spend.jsonl")
        caps = {"per_call": 1.0, "per_session": 10.0, "per_day": 0.05}
        t = BudgetTracker(session_id="day-test", caps=caps, spend_log=log)

        # Record spend that exceeds the daily cap.
        t.record_spend(
            role="test",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.05,
        )

        with pytest.raises(PerDayCapExceeded) as exc_info:
            t.check_budget(estimated_cost=0.005)
        assert exc_info.value.day_spend >= 0.05
        assert exc_info.value.cap == 0.05

    def test_day_cap_is_budget_error(self, tmp_path: Path) -> None:
        """PerDayCapExceeded should be a subclass of BudgetError."""
        log = SpendLog(log_path=tmp_path / "day-spend2.jsonl")
        caps = {"per_call": 1.0, "per_session": 10.0, "per_day": 0.01}
        t = BudgetTracker(session_id="day-err", caps=caps, spend_log=log)
        t.record_spend(
            role="test", input_tokens=10, output_tokens=5, cost_usd=0.02
        )
        with pytest.raises(BudgetError):
            t.check_budget(estimated_cost=0.005)

    def test_is_day_cap_exceeded(self, tmp_path: Path) -> None:
        """is_day_cap_exceeded returns True when over limit."""
        log = SpendLog(log_path=tmp_path / "day-check.jsonl")
        caps = {"per_call": 1.0, "per_session": 10.0, "per_day": 0.05}
        t = BudgetTracker(session_id="daycheck", caps=caps, spend_log=log)
        assert not t.is_day_cap_exceeded()
        t.record_spend(
            role="test", input_tokens=10, output_tokens=5, cost_usd=0.06
        )
        assert t.is_day_cap_exceeded()

    def test_day_cap_message(self, tmp_path: Path) -> None:
        """get_day_cap_message returns a message when daily cap is hit."""
        log = SpendLog(log_path=tmp_path / "day-msg.jsonl")
        caps = {"per_call": 1.0, "per_session": 10.0, "per_day": 0.02}
        t = BudgetTracker(session_id="daymsg", caps=caps, spend_log=log)

        assert t.get_day_cap_message() is None

        t.record_spend(
            role="test", input_tokens=10, output_tokens=5, cost_usd=0.03
        )
        msg = t.get_day_cap_message()
        assert msg is not None
        assert "$0.02" in msg
        assert "disabled" in msg.lower()

    def test_old_spend_outside_window_ignored(self, tmp_path: Path) -> None:
        """Spend older than 24 hours should not count toward the daily cap."""
        log_path = tmp_path / "old-spend.jsonl"
        # Write an entry 25 hours ago directly.
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        entry = {
            "timestamp": old_ts,
            "session_id": "old-session",
            "role": "test",
            "model": "test",
            "input_tokens": 100,
            "output_tokens": 50,
            "cost_usd": 4.00,
        }
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w") as f:
            f.write(json.dumps(entry) + "\n")

        log = SpendLog(log_path=log_path)
        caps = {"per_call": 1.0, "per_session": 10.0, "per_day": 5.00}
        t = BudgetTracker(session_id="new", caps=caps, spend_log=log)

        # Old $4.00 should be outside the window.
        assert not t.is_day_cap_exceeded()
        t.check_budget(estimated_cost=0.01)  # Should not raise.

    def test_cross_session_day_cap(self, tmp_path: Path) -> None:
        """Day cap counts spend from all sessions in the window."""
        log = SpendLog(log_path=tmp_path / "cross-session.jsonl")
        caps = {"per_call": 1.0, "per_session": 10.0, "per_day": 0.10}

        # Session A spends $0.06.
        t1 = BudgetTracker(session_id="sess-a", caps=caps, spend_log=log)
        t1.record_spend(
            role="test", input_tokens=10, output_tokens=5, cost_usd=0.06
        )

        # Session B should see Session A's spend.
        t2 = BudgetTracker(session_id="sess-b", caps=caps, spend_log=log)
        t2.record_spend(
            role="test", input_tokens=10, output_tokens=5, cost_usd=0.05
        )

        # Total: $0.11, cap is $0.10.
        with pytest.raises(PerDayCapExceeded):
            t2.check_budget(estimated_cost=0.005)


# ── Spend log tests ─────────────────────────────────────────────────────────


class TestSpendLog:
    def test_append_and_read(self, tmp_log: SpendLog) -> None:
        """Entries appended can be read back."""
        tmp_log.append(
            session_id="s1",
            role="station-ai",
            input_tokens=200,
            output_tokens=100,
            cost_usd=0.01,
            model="claude-sonnet-4-5",
        )
        entries = list(tmp_log.iter_entries())
        assert len(entries) == 1
        assert entries[0]["session_id"] == "s1"
        assert entries[0]["cost_usd"] == 0.01
        assert entries[0]["input_tokens"] == 200

    def test_multiple_entries(self, tmp_log: SpendLog) -> None:
        """Multiple entries accumulate correctly."""
        for i in range(5):
            tmp_log.append(
                session_id=f"s{i}",
                role="test",
                input_tokens=10,
                output_tokens=5,
                cost_usd=0.005,
            )
        entries = list(tmp_log.iter_entries())
        assert len(entries) == 5

    def test_rolling_24h(self, tmp_log: SpendLog) -> None:
        """rolling_24h_spend sums recent entries."""
        for _ in range(3):
            tmp_log.append(
                session_id="s1",
                role="test",
                input_tokens=10,
                output_tokens=5,
                cost_usd=0.10,
            )
        assert tmp_log.rolling_24h_spend() == pytest.approx(0.30)

    def test_sessions_summary(self, tmp_log: SpendLog) -> None:
        """sessions_summary groups by session_id."""
        for i in range(3):
            tmp_log.append(
                session_id="alpha",
                role="test",
                input_tokens=10,
                output_tokens=5,
                cost_usd=0.01,
            )
        tmp_log.append(
            session_id="beta",
            role="test",
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.05,
        )
        summary = tmp_log.sessions_summary()
        assert len(summary) == 2
        alpha = next(s for s in summary if s["session_id"] == "alpha")
        assert alpha["total_calls"] == 3
        assert alpha["total_cost"] == pytest.approx(0.03)

    def test_empty_log(self, tmp_path: Path) -> None:
        """An empty/nonexistent log returns zeros."""
        log = SpendLog(log_path=tmp_path / "nonexistent.jsonl")
        assert log.rolling_24h_spend() == 0.0
        assert log.rolling_24h_calls() == 0
        assert list(log.iter_entries()) == []

    def test_malformed_lines_skipped(self, tmp_path: Path) -> None:
        """Malformed JSON lines are silently skipped."""
        log_path = tmp_path / "bad.jsonl"
        with open(log_path, "w") as f:
            f.write("not json\n")
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "ok",
                "role": "test",
                "cost_usd": 0.01,
            }) + "\n")
            f.write("{truncated\n")
        log = SpendLog(log_path=log_path)
        entries = list(log.iter_entries())
        assert len(entries) == 1
        assert entries[0]["session_id"] == "ok"


# ── Config loading tests ────────────────────────────────────────────────────


class TestConfigLoading:
    def test_load_from_toml(self) -> None:
        """load_caps reads values from config/ai.toml."""
        config_path = Path(__file__).resolve().parent.parent / "config" / "ai.toml"
        caps = load_caps(config_path)
        assert caps["per_call"] == 0.02
        assert caps["per_session"] == 0.25
        assert caps["per_day"] == 5.00

    def test_env_var_overrides(self, tmp_path: Path) -> None:
        """Environment variables override TOML values."""
        # Write a minimal TOML config.
        toml_path = tmp_path / "ai.toml"
        toml_path.write_text("[caps]\nper_call = 0.02\nper_session = 0.25\nper_day = 5.0\n")

        env = {
            "MIRSEND_CAP_PER_CALL": "0.05",
            "MIRSEND_CAP_PER_SESSION": "1.00",
            "MIRSEND_CAP_PER_DAY": "10.00",
        }
        with patch.dict(os.environ, env):
            caps = load_caps(toml_path)
        assert caps["per_call"] == 0.05
        assert caps["per_session"] == 1.00
        assert caps["per_day"] == 10.00

    def test_missing_config_uses_defaults(self, tmp_path: Path) -> None:
        """If the TOML file doesn't exist, defaults are used."""
        caps = load_caps(tmp_path / "nonexistent.toml")
        assert caps["per_call"] == 0.02
        assert caps["per_session"] == 0.25
        assert caps["per_day"] == 5.00

    def test_partial_env_override(self, tmp_path: Path) -> None:
        """Only the env vars that are set override; others keep TOML values."""
        toml_path = tmp_path / "ai.toml"
        toml_path.write_text("[caps]\nper_call = 0.02\nper_session = 0.25\nper_day = 5.0\n")

        with patch.dict(os.environ, {"MIRSEND_CAP_PER_SESSION": "0.50"}, clear=False):
            caps = load_caps(toml_path)
        assert caps["per_call"] == 0.02
        assert caps["per_session"] == 0.50
        assert caps["per_day"] == 5.00


# ── First-contact notice tests ──────────────────────────────────────────────


class TestFirstContactNotice:
    def test_fires_once(self, tracker: BudgetTracker) -> None:
        """First-contact notice should fire exactly once."""
        notice = tracker.get_first_contact_notice()
        assert notice is not None
        assert "$0.25" in notice
        assert "docs/ai-setup.md" in notice

        # Second call returns None.
        assert tracker.get_first_contact_notice() is None

    def test_notice_includes_cap(self, tmp_path: Path) -> None:
        """Notice includes the per-session cap value."""
        log = SpendLog(log_path=tmp_path / "notice.jsonl")
        caps = {"per_call": 0.02, "per_session": 0.50, "per_day": 5.00}
        t = BudgetTracker(session_id="notice-test", caps=caps, spend_log=log)
        notice = t.get_first_contact_notice()
        assert "$0.50" in notice


# ── Degraded-mode integration tests ─────────────────────────────────────────


class TestDegradedMode:
    def test_game_continues_after_degraded(
        self, tight_tracker: BudgetTracker
    ) -> None:
        """The tracker enters degraded mode but doesn't crash or throw
        unexpected errors — it consistently rejects with PerSessionCapExceeded."""
        # Exhaust the session cap.
        for _ in range(3):
            tight_tracker.check_budget(estimated_cost=0.01)
            tight_tracker.record_spend(
                role="station-ai",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )
        assert tight_tracker.is_degraded

        # Multiple subsequent calls all raise PerSessionCapExceeded.
        for _ in range(5):
            with pytest.raises(PerSessionCapExceeded):
                tight_tracker.check_budget(estimated_cost=0.001)

    def test_degraded_message_content(
        self, tight_tracker: BudgetTracker
    ) -> None:
        """The canned message matches the expected in-fiction text."""
        for _ in range(3):
            tight_tracker.check_budget(estimated_cost=0.01)
            tight_tracker.record_spend(
                role="station-ai",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )
        msg = tight_tracker.get_degraded_message()
        assert msg == "Argon-87's voice cuts out. Power rationing protocol."

    def test_no_api_call_after_any_cap(self, tmp_path: Path) -> None:
        """Verify that check_budget always raises after any cap is hit,
        meaning no API call can ever fire."""
        log = SpendLog(log_path=tmp_path / "no-api.jsonl")

        # Test with per-session cap.
        caps = {"per_call": 1.0, "per_session": 0.02, "per_day": 10.0}
        t = BudgetTracker(session_id="no-api", caps=caps, spend_log=log)
        t.record_spend(
            role="test", input_tokens=10, output_tokens=5, cost_usd=0.02
        )

        # Every subsequent check_budget must raise.
        api_called = False
        for _ in range(10):
            try:
                t.check_budget(estimated_cost=0.001)
                api_called = True  # This should never execute.
            except BudgetError:
                pass
        assert not api_called, "API call would have fired past the cap"


# ── Report script tests ─────────────────────────────────────────────────────


class TestReportScript:
    @staticmethod
    def _load_report_module():
        """Import ai-spend.py as a module."""
        import importlib.util
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
        spec = importlib.util.spec_from_file_location(
            "ai_spend",
            scripts_dir / "ai-spend.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_report_no_log(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Report script handles missing log gracefully."""
        mod = self._load_report_module()
        log = SpendLog(log_path=tmp_path / "empty.jsonl")
        with patch.object(mod, "SpendLog", return_value=log):
            mod.main()

        captured = capsys.readouterr()
        assert "No spend log found" in captured.out

    def test_report_with_data(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Report script formats spend data correctly."""
        log_path = tmp_path / "report-data.jsonl"
        log = SpendLog(log_path=log_path)

        # Add some entries.
        for i in range(5):
            log.append(
                session_id="report-sess",
                role="test",
                input_tokens=100,
                output_tokens=50,
                cost_usd=0.01,
            )

        mod = self._load_report_module()
        with patch.object(mod, "SpendLog", return_value=log):
            mod.main()

        captured = capsys.readouterr()
        assert "Last 24 hours:" in captured.out
        assert "$0.05" in captured.out
        assert "5 calls" in captured.out
