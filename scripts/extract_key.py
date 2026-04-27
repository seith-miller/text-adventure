#!/usr/bin/env python3
"""
One-time KeePass extractor for ANTHROPIC_API_KEY.

Prompts for the master password, extracts the API key, writes it to
`.env.playtest` at the repo root with mode 0600. The file is ignored
by git. Source it in any shell that needs the key:

    set -a && . .env.playtest && set +a

Or pass it to scripts that read env files directly.
"""

from __future__ import annotations

import getpass
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from launch import extract_api_key  # noqa: E402

DEFAULT_KDBX = pathlib.Path.home() / "seith-keys.kdbx"
DEFAULT_ENTRY = "mirs-end-in-game"
ENV_FILE = REPO_ROOT / ".env.playtest"


def main() -> int:
    pw = getpass.getpass("KeePass master password: ")
    key = extract_api_key(DEFAULT_KDBX, DEFAULT_ENTRY, pw)

    ENV_FILE.write_text(f'ANTHROPIC_API_KEY="{key}"\n')
    os.chmod(ENV_FILE, 0o600)
    print(f"Wrote {ENV_FILE} (mode 0600).", flush=True)
    print(
        "Source it before running tools that need the key:\n"
        f"  set -a && . {ENV_FILE.relative_to(REPO_ROOT)} && set +a",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
