#!/usr/bin/env python3
"""Launch the local play environment: static server + ingest proxy.

Starts:
  - python http.server on port 8181 (serves game/, where play.html lives)
  - scripts/ai-proxy.py on port 8787 (accepts /v1/sessions ingest, optionally /v1/call)

Logs both subprocess streams to stdout with a [static] / [proxy] prefix.
Ctrl-C reaps both cleanly.

Without ANTHROPIC_API_KEY, the proxy still starts — /v1/call returns 503 but
/v1/sessions writes to data/playthroughs.sqlite. With the key set, Argon-87
also works.

Usage:
    python3 scripts/launch-local.py
    # then open http://localhost:8181/play.html
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _stream(proc: subprocess.Popen, prefix: str) -> None:
    """Forward a subprocess's combined output to our stdout with a prefix."""
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip()
        if line:
            print(f"[{prefix}] {line}", flush=True)


def main() -> int:
    static_cmd = [
        sys.executable,
        "-m",
        "http.server",
        "8181",
        "--directory",
        str(ROOT / "game"),
    ]
    proxy_cmd = [sys.executable, str(ROOT / "scripts" / "ai-proxy.py")]

    print("[launch] starting static server on http://localhost:8181 ...", flush=True)
    static = subprocess.Popen(
        static_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    threading.Thread(target=_stream, args=(static, "static"), daemon=True).start()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "[launch] ANTHROPIC_API_KEY not set — Argon-87 (/v1/call) will return 503. "
            "Session ingest (/v1/sessions → data/playthroughs.sqlite) still works.",
            flush=True,
        )

    print("[launch] starting ingest proxy on http://127.0.0.1:8787 ...", flush=True)
    proxy = subprocess.Popen(
        proxy_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    threading.Thread(target=_stream, args=(proxy, "proxy"), daemon=True).start()

    print(
        "[launch] both up. Open http://localhost:8181/play.html "
        "— Ctrl-C here to stop both.",
        flush=True,
    )

    def _shutdown(*_: object) -> None:
        for name, proc in (("static", static), ("proxy", proxy)):
            if proc.poll() is None:
                print(f"[launch] terminating {name} ...", flush=True)
                proc.terminate()
        for proc in (static, proxy):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Block until either subprocess exits. If one crashes, take the other down.
    while True:
        for name, proc in (("static", static), ("proxy", proxy)):
            rc = proc.poll()
            if rc is not None:
                print(f"[launch] {name} exited with code {rc}", flush=True)
                _shutdown()
                return rc or 1
        try:
            signal.pause()
        except KeyboardInterrupt:
            _shutdown()
            return 0


if __name__ == "__main__":
    sys.exit(main())
