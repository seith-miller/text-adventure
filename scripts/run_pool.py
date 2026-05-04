#!/usr/bin/env python3
"""
Convenience wrapper for AI playtest runs.

Prompts for the KeePass master password, extracts ANTHROPIC_API_KEY,
then invokes the playtest pool runner with whatever args you pass.

Usage:
    python scripts/run_pool.py [-- pool args...]

Examples:
    # Smoke test: 1 run, 30 turns
    python scripts/run_pool.py --runs 1 --max-turns 30 --concurrency 1 --budget 0.50

    # Real run: 8 runs, 4 at a time, $5 cap
    python scripts/run_pool.py --runs 8 --concurrency 4 --max-turns 100 --budget 5.00
"""

from __future__ import annotations

import getpass
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from launch import extract_api_key  # noqa: E402

DEFAULT_KDBX = pathlib.Path.home() / "seith-keys.kdbx"
DEFAULT_ENTRY = "mirs-end-in-game"


def main() -> int:
    pool_args = sys.argv[1:]
    if not pool_args:
        pool_args = ["--runs", "1", "--max-turns", "30",
                     "--concurrency", "1", "--budget", "0.50"]
        print(f"(no args provided; using smoke defaults: {' '.join(pool_args)})",
              flush=True)

    pw = getpass.getpass("KeePass master password: ")
    key = extract_api_key(DEFAULT_KDBX, DEFAULT_ENTRY, pw)

    env = {**os.environ, "ANTHROPIC_API_KEY": key}
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "playtest-pool.py"),
           "run", *pool_args]
    print(f"$ {' '.join(cmd[1:])}", flush=True)
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
