#!/usr/bin/env python3
"""
Launch MIR'S END with AI features enabled.

Prompts for the KeePass master password, extracts the Anthropic API key
from the configured entry, then starts the proxy server and the static
web server with the key in their environment.

The Anthropic key never touches stdout, log files, or disk. It exists
only as an in-memory string between extraction and child-process spawn,
then only in the env vars of the subprocesses.

## Configuration (env vars; sensible defaults if absent)

- MIRSEND_KEEPASS_PATH    Path to .kdbx file. Default: ~/seith-keys.kdbx
- MIRSEND_KEEPASS_ENTRY   Entry title. Default: mirs-end-in-game
- MIRSEND_PROXY_PORT      Default: 8787
- MIRSEND_WEB_PORT        Default: 8080
- MIRSEND_SKIP_BUILD      If "1", skip `npm run build:story`
- MIRSEND_AI_ENABLED      If "0", skip KeePass and proxy entirely

## Exit codes

  0  clean shutdown (Ctrl+C or one child exited)
  2  KeePass database missing
  3  wrong KeePass master password
  4  entry not found in database
  5  entry has no password field
  10 story build failed
  11 proxy failed to start
  12 web server failed to start
  13 child died unexpectedly during run
"""

from __future__ import annotations

import getpass
import os
import pathlib
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_KEEPASS_PATH = pathlib.Path.home() / "seith-keys.kdbx"
DEFAULT_KEEPASS_ENTRY = "mirs-end-in-game"
DEFAULT_PROXY_PORT = 8787
DEFAULT_WEB_PORT = 8080
GAME_DIR = REPO_ROOT / "game"


def _load_config() -> dict:
    return {
        "keepass_path": pathlib.Path(
            os.environ.get("MIRSEND_KEEPASS_PATH", str(DEFAULT_KEEPASS_PATH))
        ).expanduser(),
        "keepass_entry": os.environ.get("MIRSEND_KEEPASS_ENTRY", DEFAULT_KEEPASS_ENTRY),
        "proxy_port": int(os.environ.get("MIRSEND_PROXY_PORT", DEFAULT_PROXY_PORT)),
        "web_port": int(os.environ.get("MIRSEND_WEB_PORT", DEFAULT_WEB_PORT)),
        "skip_build": os.environ.get("MIRSEND_SKIP_BUILD") == "1",
        "ai_enabled": os.environ.get("MIRSEND_AI_ENABLED", "1") != "0",
    }


def extract_api_key(
    db_path: pathlib.Path, entry_title: str, master_password: str
) -> str:
    """
    Open a KeePass database and return the password field of the named entry.

    Raises:
      FileNotFoundError    db file does not exist
      ValueError           wrong master password
      LookupError          entry not found, or entry has no password
    """
    if not db_path.is_file():
        raise FileNotFoundError(f"KeePass database not found: {db_path}")

    # Imported here so the script can run without pykeepass installed when
    # AI is disabled.
    from pykeepass import PyKeePass  # noqa: PLC0415
    from pykeepass.exceptions import CredentialsError  # noqa: PLC0415

    try:
        kp = PyKeePass(str(db_path), password=master_password)
    except CredentialsError as exc:
        raise ValueError("incorrect master password") from exc

    entry = kp.find_entries(title=entry_title, first=True)
    if entry is None:
        titles = sorted({e.title for e in kp.entries if e.title})
        raise LookupError(
            f"entry {entry_title!r} not found. "
            f"Available entries: {', '.join(titles) if titles else '(none)'}"
        )

    api_key = entry.password
    if not api_key:
        raise LookupError(f"entry {entry_title!r} has no password field")
    return api_key


def _build_story() -> None:
    print("Building story...", flush=True)
    result = subprocess.run(
        ["npm", "run", "build:story"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(10)
    print("✓ Built story.ulx", flush=True)


def _start_proxy(api_key: str, port: int) -> subprocess.Popen:
    """
    Spawn the proxy server with the API key in its env. The proxy entry
    point is part of #65; until that lands the launcher tolerates a
    placeholder script. We try the canonical entry first, fall back to
    a one-line placeholder if it does not exist.
    """
    env = {**os.environ, "ANTHROPIC_API_KEY": api_key, "PORT": str(port)}
    canonical = REPO_ROOT / "scripts" / "ai_proxy.py"
    if canonical.is_file():
        cmd = [sys.executable, str(canonical)]
    else:
        # Placeholder until #65 lands. The proxy script is missing;
        # spawn a process that fails fast so the launcher exits.
        sys.stderr.write(
            f"warning: {canonical} does not exist yet (m10 #65 has not landed). "
            "Launcher will start without a working proxy; AI features will fall "
            "back to the canned offline message.\n"
        )
        cmd = [
            sys.executable,
            "-c",
            f"import http.server,socketserver;"
            f"socketserver.TCPServer(('localhost',{port}),"
            f"http.server.BaseHTTPRequestHandler).serve_forever()",
        ]
    proc = subprocess.Popen(cmd, env=env, cwd=str(REPO_ROOT))  # noqa: S603
    return proc


def _start_web_server(port: int) -> subprocess.Popen:
    cmd = [sys.executable, "-m", "http.server", str(port)]
    proc = subprocess.Popen(cmd, cwd=str(GAME_DIR))  # noqa: S603
    return proc


@contextmanager
def _children(procs: list[subprocess.Popen]):
    try:
        yield
    finally:
        for p in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
        # Give them a moment to shut down gracefully, then kill.
        deadline = time.time() + 5
        for p in procs:
            remaining = deadline - time.time()
            if remaining > 0:
                try:
                    p.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    p.kill()
            elif p.poll() is None:
                p.kill()


def main() -> int:
    cfg = _load_config()

    if not cfg["ai_enabled"]:
        print("MIRSEND_AI_ENABLED=0; skipping KeePass + proxy.")
        if not cfg["skip_build"]:
            _build_story()
        web = _start_web_server(cfg["web_port"])
        with _children([web]):
            try:
                web.wait()
            except KeyboardInterrupt:
                pass
        return 0

    # Extract the API key.
    try:
        master = getpass.getpass("KeePass master password: ")
    except (KeyboardInterrupt, EOFError):
        print()
        return 0

    try:
        api_key: Optional[str] = extract_api_key(
            cfg["keepass_path"], cfg["keepass_entry"], master
        )
    except FileNotFoundError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 3
    except LookupError as exc:
        sys.stderr.write(f"{exc}\n")
        return 4
    finally:
        # Best-effort scrub of the master password from the local var.
        master = "x" * len(master)
        del master

    print(f"✓ Extracted ANTHROPIC_API_KEY from entry {cfg['keepass_entry']!r}")

    if not cfg["skip_build"]:
        _build_story()

    # Spawn children with the key in env.
    proxy = _start_proxy(api_key, cfg["proxy_port"])
    if proxy.poll() is not None:
        sys.stderr.write("proxy failed to start\n")
        return 11
    print(f"✓ Starting proxy on localhost:{cfg['proxy_port']} (pid {proxy.pid})")

    web = _start_web_server(cfg["web_port"])
    if web.poll() is not None:
        proxy.terminate()
        sys.stderr.write("web server failed to start\n")
        return 12
    print(f"✓ Starting web server on localhost:{cfg['web_port']} (pid {web.pid})")

    # Scrub the api_key from the launcher's own variable.
    api_key = "x" * len(api_key) if api_key else api_key
    del api_key

    print()
    print(f"Open http://localhost:{cfg['web_port']}/play.html to play.")
    print()
    print("Press Ctrl+C to stop both servers.")

    with _children([proxy, web]):
        try:
            while proxy.poll() is None and web.poll() is None:
                time.sleep(0.5)
        except KeyboardInterrupt:
            return 0
        return 13


if __name__ == "__main__":
    raise SystemExit(main())
