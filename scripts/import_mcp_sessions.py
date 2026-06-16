#!/usr/bin/env python3
"""Import MIR'S END playtest transcripts into data/playthroughs.sqlite.

The browser-side `postSession()` path and `playtest.py --post-to`
both POST to `/v1/sessions`. MCP-driven playthroughs that were saved
to disk with `playtest.py --output <path>` (or pool-runner JSONs) bypass
the HTTP path. This script reads those exported JSON files and writes
them through the SAME normalization that `/v1/sessions` uses, so the
two ingest surfaces stay in lockstep on schema.

Usage:
    python3 scripts/import_mcp_sessions.py data/playtests/*.json
    python3 scripts/import_mcp_sessions.py 'data/playtests/*.json'   # quoted glob OK
    python3 scripts/import_mcp_sessions.py data/playtests/one.json

Exit code is the number of files that failed (0 means all imported,
non-zero is a per-file failure count). Per-file errors are reported on
stderr and do not abort the batch.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.playthrough_db import normalize_session_payload, write_session  # noqa: E402


def _import_one(path: Path) -> dict:
    """Read one exported transcript and write it to the DB.

    Returns the write_session counts (e.g. `{sessions: 1, turns: 42, ...}`).
    """
    body = json.loads(path.read_text(encoding="utf-8"))
    # Treat the on-disk file as one valid payload shape for /v1/sessions.
    # If the file lacks `session_id`, fall back to the filename stem —
    # downstream re-imports of the same file remain idempotent because
    # write_session keys on session_id.
    body.setdefault("session_id", path.stem)
    payload = normalize_session_payload(body)
    return write_session(payload)


def _expand_args(args: list[str]) -> list[Path]:
    """Expand each argv entry through `glob` (so quoted globs work) and
    return concrete Paths. Argv entries that don't match anything are
    surfaced as-is so the caller sees a 'no such file' error rather than
    a silent empty-batch."""
    out: list[Path] = []
    for arg in args:
        matches = glob.glob(arg)
        if matches:
            out.extend(Path(m) for m in matches)
        else:
            # Pass through unmatched literal so the per-file open()
            # raises FileNotFoundError with a real error message.
            out.append(Path(arg))
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: import_mcp_sessions.py <path-or-glob>...",
            file=sys.stderr,
        )
        return 1

    failures = 0
    paths = _expand_args(sys.argv[1:])
    if not paths:
        print("no input files", file=sys.stderr)
        return 1

    for path in paths:
        try:
            counts = _import_one(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"failed: {path} — {exc}", file=sys.stderr)
            failures += 1
            continue
        print(f"imported: {path.name} — {counts}")
    return failures


if __name__ == "__main__":
    sys.exit(main())
