#!/usr/bin/env python3
"""
Parallel playtest runner + reporting.

Spawns N concurrent sandboxed playtest drivers (per scripts/playtest.py)
and writes each completed run to the playthrough database. Then emits a
markdown report aggregating the corpus.

## Usage

```
# Run 16 playthroughs, 4 at a time, each capped at 100 turns.
python3 scripts/playtest-pool.py run --runs 16 --concurrency 4 --max-turns 100

# Emit a markdown report from the existing DB rows.
python3 scripts/playtest-pool.py report --player-kind agent:claude-sonnet-4-5
```

## Concurrency model

Each driver instance uses Playwright internally; running them in
threads in one process risks Playwright/asyncio cross-contamination.
We use subprocess isolation via `concurrent.futures.ProcessPoolExecutor`,
where each worker invokes `scripts/playtest.py` and produces a JSON
summary which we ingest after the worker exits.

## Cost guard

If `MIRSEND_QA_BUDGET_USD` is set, the pool stops queueing new runs
once the cumulative cost exceeds that budget. The currently running
batch finishes, then the pool exits cleanly with the rows it has.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import uuid
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from lib.playthrough_db import (  # noqa: E402
    commands_attempted,
    ending_distribution,
    session_summaries,
    stuck_moments,
    turns_to_first_argon_call,
    unrecognized_commands,
    write_session,
)

DEFAULT_RUNS = 4
DEFAULT_CONCURRENCY = 4
DEFAULT_MAX_TURNS = 100
DEFAULT_STUCK_WINDOW = 10
DEFAULT_MODEL = "claude-sonnet-4-5"


def _run_one_driver(
    *,
    model: str,
    max_turns: int,
    stuck_window: int,
    output_path: str,
    timeout: int,
) -> dict:
    """
    Run scripts/playtest.py as a subprocess with --output and return the
    parsed summary. The driver writes its own output JSON to disk; we
    read it back to avoid stdout-parsing fragility.
    """
    script = REPO_ROOT / "scripts" / "playtest.py"
    cmd = [
        sys.executable,
        str(script),
        "--model", model,
        "--max-turns", str(max_turns),
        "--stuck-window", str(stuck_window),
        "--no-ingest",
        "--output", output_path,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "stdout": "", "stderr": ""}

    if proc.returncode != 0:
        return {
            "error": f"driver exit {proc.returncode}",
            "stdout": proc.stdout[-2000:],
            "stderr": proc.stderr[-2000:],
        }
    try:
        return json.loads(pathlib.Path(output_path).read_text())
    except (FileNotFoundError, ValueError) as exc:
        return {
            "error": f"output parse: {exc}",
            "stdout": proc.stdout[-2000:],
            "stderr": proc.stderr[-2000:],
        }


def _ingest_summary(summary: dict, db_path: Optional[pathlib.Path]) -> bool:
    """Translate a driver summary into write_session shape and persist."""
    if "error" in summary:
        return False
    payload = {
        "session_id": summary["session_id"],
        "started_at": summary.get("started_at"),
        "ended_at": summary.get("ended_at"),
        "status": summary.get("status", "abandoned"),
        "ending_type": summary.get("ending_type"),
        "final_score": summary.get("final_score"),
        "final_o2": summary.get("final_o2"),
        "final_morale": summary.get("final_morale"),
        "player_kind": summary.get("player_kind", f"agent:{summary.get('model', 'unknown')}"),
        "game_version": summary.get("game_version", "develop"),
        "turns": summary.get("turns") or [],
        "metadata": summary.get("metadata") or {},
    }
    write_session(payload, db_path=db_path)
    return True


def run_pool(
    *,
    runs: int,
    concurrency: int,
    model: str,
    max_turns: int,
    stuck_window: int,
    timeout: int,
    db_path: Optional[pathlib.Path] = None,
    budget_usd: Optional[float] = None,
) -> dict:
    """Run `runs` playthroughs `concurrency` at a time. Returns aggregate stats."""
    print(
        f"Pool start: runs={runs} concurrency={concurrency} model={model}",
        flush=True,
    )

    started = time.time()
    submitted = 0
    completed = 0
    ingested = 0
    failures: list[str] = []
    cumulative_cost = 0.0

    with tempfile.TemporaryDirectory() as tmp_root:
        tmp_dir = pathlib.Path(tmp_root)
        with ProcessPoolExecutor(max_workers=concurrency) as ex:
            futures: dict = {}
            while submitted < runs or futures:
                # Top up the pool unless we've hit the budget cap.
                while (
                    submitted < runs
                    and len(futures) < concurrency
                    and (budget_usd is None or cumulative_cost < budget_usd)
                ):
                    out = tmp_dir / f"summary-{uuid.uuid4().hex[:8]}.json"
                    fut = ex.submit(
                        _run_one_driver,
                        model=model,
                        max_turns=max_turns,
                        stuck_window=stuck_window,
                        output_path=str(out),
                        timeout=timeout,
                    )
                    futures[fut] = out
                    submitted += 1

                if not futures:
                    break

                # Wait for at least one to finish.
                done = next(as_completed(futures))
                out_path = futures.pop(done)
                summary = done.result()
                completed += 1

                if "error" in summary:
                    failures.append(summary.get("error", "unknown"))
                    print(
                        f"  [{completed}/{runs}] FAIL: {summary.get('error')}",
                        flush=True,
                    )
                    continue

                cost = float(summary.get("estimated_cost_usd", 0.0) or 0.0)
                cumulative_cost += cost
                if _ingest_summary(summary, db_path=db_path):
                    ingested += 1
                print(
                    f"  [{completed}/{runs}] {summary.get('bailout_reason')}, "
                    f"turns={summary.get('turns_count')}, "
                    f"ending={summary.get('ending_type')}, "
                    f"cost=${cost:.4f}",
                    flush=True,
                )

                if budget_usd is not None and cumulative_cost >= budget_usd:
                    print(
                        f"  budget cap hit (${cumulative_cost:.2f} ≥ "
                        f"${budget_usd:.2f}); halting new dispatches",
                        flush=True,
                    )

    elapsed = time.time() - started
    print(
        f"Pool done: completed={completed} ingested={ingested} "
        f"failures={len(failures)} cost=${cumulative_cost:.4f} "
        f"elapsed={elapsed:.1f}s",
        flush=True,
    )
    return {
        "runs_submitted": submitted,
        "runs_completed": completed,
        "runs_ingested": ingested,
        "failures": failures,
        "total_cost_usd": round(cumulative_cost, 4),
        "elapsed_seconds": round(elapsed, 1),
    }


def render_report(
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
    top_n: int = 10,
) -> str:
    """Build a markdown report from the playthrough DB."""
    summary = session_summaries(player_kind, since, db_path=db_path)
    endings = ending_distribution(player_kind, since, db_path=db_path)
    stuck = stuck_moments(player_kind, since, db_path=db_path)
    unrec = unrecognized_commands(player_kind, since, db_path=db_path)
    cmds = commands_attempted(player_kind, since, db_path=db_path)
    argon_turns = turns_to_first_argon_call(player_kind, since, db_path=db_path)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = summary["total"] or 1  # avoid div-by-zero when totals are 0
    by_status = summary["by_status"]

    lines: list[str] = []
    lines.append(f"# Playtest pool report - {today}")
    if player_kind:
        lines.append(f"_Filter: player_kind = {player_kind}_")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Runs: {summary['total']}")
    lines.append(f"- Completed (reached ending): {by_status.get('completed', 0)}")
    lines.append(f"- Stuck-loop bailouts: {by_status.get('stuck', 0)}")
    lines.append(f"- Abandoned: {by_status.get('abandoned', 0)}")
    lines.append(f"- Total cost: ${summary['total_cost_usd']:.2f}")
    lines.append("")

    lines.append("## Endings")
    if endings:
        for key, count in endings.most_common():
            pct = round(100 * count / total)
            lines.append(f"- {key}: {count} ({pct}%)")
    else:
        lines.append("- (none)")
    lines.append("")

    lines.append("## Top stuck rooms")
    if stuck:
        for room, count in stuck.most_common(top_n):
            lines.append(f"- {room}: {count} sessions")
    else:
        lines.append("- (no stuck-loop bailouts recorded)")
    lines.append("")

    lines.append("## Top unrecognized commands")
    if unrec:
        for cmd, count in unrec.most_common(top_n):
            lines.append(f"- {cmd!r}: {count} attempts")
    else:
        lines.append("- (none detected)")
    lines.append("")

    lines.append("## Top commands attempted")
    if cmds:
        for cmd, count in cmds.most_common(top_n):
            lines.append(f"- {cmd!r}: {count}")
    else:
        lines.append("- (no commands recorded)")
    lines.append("")

    lines.append("## Argon engagement")
    if argon_turns:
        avg = sum(argon_turns) / len(argon_turns)
        lines.append(
            f"- Sessions that called Argon: {len(argon_turns)} / {summary['total']}"
        )
        lines.append(f"- First call (median turn): {sorted(argon_turns)[len(argon_turns) // 2]}")
        lines.append(f"- First call (average turn): {avg:.1f}")
    else:
        lines.append(
            f"- Sessions that called Argon: 0 / {summary['total']}"
        )
    lines.append("")

    return "\n".join(lines)


def cmd_run(args: argparse.Namespace) -> int:
    budget_env = os.environ.get("MIRSEND_QA_BUDGET_USD")
    budget_usd: Optional[float] = float(budget_env) if budget_env else None
    if args.budget is not None:
        budget_usd = args.budget

    db_path = pathlib.Path(args.db).expanduser() if args.db else None

    run_pool(
        runs=args.runs,
        concurrency=args.concurrency,
        model=args.model,
        max_turns=args.max_turns,
        stuck_window=args.stuck_window,
        timeout=args.timeout,
        db_path=db_path,
        budget_usd=budget_usd,
    )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    db_path = pathlib.Path(args.db).expanduser() if args.db else None
    report = render_report(
        player_kind=args.player_kind,
        since=args.since,
        db_path=db_path,
        top_n=args.top_n,
    )
    if args.output:
        pathlib.Path(args.output).write_text(report)
        print(f"Report written to {args.output}", flush=True)
    else:
        print(report)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pool runner + report formatter for AI playtests."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run N playthroughs and ingest each.")
    p_run.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    p_run.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    p_run.add_argument("--model", default=DEFAULT_MODEL)
    p_run.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    p_run.add_argument("--stuck-window", type=int, default=DEFAULT_STUCK_WINDOW)
    p_run.add_argument(
        "--timeout", type=int, default=900,
        help="Per-driver timeout in seconds.",
    )
    p_run.add_argument(
        "--budget", type=float, default=None,
        help="Per-pool budget cap in USD. Overrides MIRSEND_QA_BUDGET_USD.",
    )
    p_run.add_argument("--db", default=None, help="Override DB path.")
    p_run.set_defaults(func=cmd_run)

    p_rep = sub.add_parser("report", help="Render a markdown report.")
    p_rep.add_argument("--player-kind", default=None)
    p_rep.add_argument("--since", default=None, help="ISO 8601 timestamp.")
    p_rep.add_argument("--top-n", type=int, default=10)
    p_rep.add_argument("--output", default=None, help="Write report to file.")
    p_rep.add_argument("--db", default=None, help="Override DB path.")
    p_rep.set_defaults(func=cmd_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
