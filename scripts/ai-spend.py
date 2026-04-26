#!/usr/bin/env python3
"""Mir's End — AI spend report.

Reads ``logs/ai-spend.jsonl`` and prints a summary of recent spend.

Usage::

    $ python scripts/ai-spend.py
    Last 24 hours: $1.47 (68 calls)
    Last 7 days:   $8.12 (384 calls)
    Per-session average: $0.06
    Recent sessions:
      abc123  2 hours ago   $0.18  (calls: 12)
      def456  yesterday     $0.09  (calls: 8)
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path so we can import the bridge library.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "lib"))

from mirs_end_bridge.spend_log import SpendLog


def _relative_time(iso_ts: str) -> str:
    """Convert an ISO timestamp to a human-friendly relative string."""
    try:
        ts = datetime.fromisoformat(iso_ts)
    except ValueError:
        return "unknown"

    now = datetime.now(timezone.utc)
    delta = now - ts
    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    if seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(seconds / 86400)
    if days == 1:
        return "yesterday"
    return f"{days} days ago"


def main() -> None:
    log = SpendLog()

    if not log.log_path.exists():
        print("No spend log found. No AI calls have been recorded yet.")
        print(f"(Expected at: {log.log_path})")
        return

    spend_24h = log.rolling_24h_spend()
    calls_24h = log.rolling_24h_calls()
    spend_7d = log.rolling_7d_spend()
    calls_7d = log.rolling_7d_calls()

    sessions = log.sessions_summary(limit=10)
    if sessions:
        avg_cost = sum(s["total_cost"] for s in sessions) / len(sessions)
    else:
        avg_cost = 0.0

    print(f"Last 24 hours: ${spend_24h:.2f} ({calls_24h} calls)")
    print(f"Last 7 days:   ${spend_7d:.2f} ({calls_7d} calls)")
    print(f"Per-session average: ${avg_cost:.2f}")

    if sessions:
        print("Recent sessions:")
        for s in sessions:
            sid = s["session_id"][:8]
            when = _relative_time(s["last_timestamp"])
            cost = s["total_cost"]
            calls = s["total_calls"]
            print(f"  {sid:<10s} {when:<18s} ${cost:.2f}  (calls: {calls})")
    else:
        print("No sessions recorded yet.")


if __name__ == "__main__":
    main()
