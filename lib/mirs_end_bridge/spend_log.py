"""Append-only spend log for Mir's End AI cost tracking.

Every Claude call is persisted as a JSON-lines entry in
``logs/ai-spend.jsonl``.  The log supports querying the rolling 24-hour
spend total and iterating over all entries for reporting.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterator

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_LOG_PATH = _PROJECT_ROOT / "logs" / "ai-spend.jsonl"


class SpendLog:
    """Thread-safe, append-only spend log backed by a JSONL file.

    Parameters
    ----------
    log_path:
        Path to the JSONL file.  Defaults to ``logs/ai-spend.jsonl``
        relative to the project root.
    """

    def __init__(self, log_path: Path | None = None) -> None:
        self.log_path = log_path or _DEFAULT_LOG_PATH
        self._lock = threading.Lock()

    def append(
        self,
        *,
        session_id: str,
        role: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        model: str = "",
    ) -> None:
        """Append a single spend entry to the log file.

        Creates the parent directory if it does not exist.
        """
        now = datetime.now(timezone.utc)
        entry = {
            "timestamp": now.isoformat(),
            "session_id": session_id,
            "role": role,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost_usd,
        }
        with self._lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def iter_entries(self) -> Iterator[dict[str, Any]]:
        """Yield all log entries as dicts, oldest first.

        Silently skips malformed lines.
        """
        if not self.log_path.exists():
            return
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

    def rolling_24h_spend(self) -> float:
        """Return total USD spent in the last 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        total = 0.0
        for entry in self.iter_entries():
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    total += entry.get("cost_usd", 0.0)
            except (KeyError, ValueError):
                continue
        return total

    def rolling_7d_spend(self) -> float:
        """Return total USD spent in the last 7 days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        total = 0.0
        for entry in self.iter_entries():
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    total += entry.get("cost_usd", 0.0)
            except (KeyError, ValueError):
                continue
        return total

    def rolling_24h_calls(self) -> int:
        """Return number of calls in the last 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        count = 0
        for entry in self.iter_entries():
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    count += 1
            except (KeyError, ValueError):
                continue
        return count

    def rolling_7d_calls(self) -> int:
        """Return number of calls in the last 7 days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        count = 0
        for entry in self.iter_entries():
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    count += 1
            except (KeyError, ValueError):
                continue
        return count

    def sessions_summary(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent session summaries, newest first.

        Each summary contains: session_id, last_timestamp, total_cost,
        total_calls.
        """
        sessions: dict[str, dict[str, Any]] = {}
        for entry in self.iter_entries():
            sid = entry.get("session_id", "unknown")
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "last_timestamp": entry.get("timestamp", ""),
                    "total_cost": 0.0,
                    "total_calls": 0,
                }
            sessions[sid]["total_cost"] += entry.get("cost_usd", 0.0)
            sessions[sid]["total_calls"] += 1
            sessions[sid]["last_timestamp"] = entry.get("timestamp", "")

        # Sort by last timestamp descending.
        sorted_sessions = sorted(
            sessions.values(),
            key=lambda s: s["last_timestamp"],
            reverse=True,
        )
        return sorted_sessions[:limit]
