#!/usr/bin/env python3
"""
Generate ``game/dist/version.json`` from package.json + git state.

Run as part of the build pipeline (after the Inform 7 compile so the
ulx hash is available). Anyone who needs to know what code produced a
playthrough reads this file: the browser, the CLI playtest driver,
and any future analysis tool.

Output schema:

    {
      "semver": "0.1.0",
      "git_sha": "f238a65",
      "git_branch": "develop",
      "dirty": false,
      "ulx_sha256": "<short>",
      "story_serial": "260428",
      "built_at": "2026-04-28T14:30:00+00:00",
      "version_string": "0.1.0+f238a65"
    }

``version_string`` is what gets stored in ``sessions.game_version`` in
the playthrough DB and is the human-friendly identifier:

    <semver>+<sha>[-dirty]
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_JSON = REPO_ROOT / "package.json"
ULX_PATH = REPO_ROOT / "game" / "dist" / "story.ulx"
VERSION_JSON = REPO_ROOT / "game" / "dist" / "version.json"


def _read_semver() -> str:
    try:
        data = json.loads(PACKAGE_JSON.read_text())
        v = data.get("version")
        if isinstance(v, str) and v.strip():
            return v.strip()
    except (OSError, ValueError):
        pass
    return "0.0.0"


def _git(*args: str) -> str:
    try:
        out = subprocess.check_output(
            ["git", *args],
            cwd=str(REPO_ROOT),
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8", errors="replace").strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _git_sha() -> str:
    return _git("rev-parse", "--short", "HEAD") or "unknown"


def _git_branch() -> str:
    return _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"


def _is_dirty() -> bool:
    """True if the working tree has uncommitted changes (staged or unstaged)."""
    return bool(_git("status", "--porcelain"))


def _ulx_sha256_short() -> str:
    if not ULX_PATH.is_file():
        return ""
    h = hashlib.sha256()
    with open(ULX_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def _story_serial() -> str:
    """The Inform 7 release serial: today's date as YYMMDD."""
    return datetime.now(timezone.utc).strftime("%y%m%d")


def build_version() -> dict:
    semver = _read_semver()
    sha = _git_sha()
    dirty = _is_dirty()

    version_string = f"{semver}+{sha}"
    if dirty:
        version_string += "-dirty"

    return {
        "semver": semver,
        "git_sha": sha,
        "git_branch": _git_branch(),
        "dirty": dirty,
        "ulx_sha256": _ulx_sha256_short(),
        "story_serial": _story_serial(),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "version_string": version_string,
    }


def main() -> int:
    info = build_version()
    VERSION_JSON.parent.mkdir(parents=True, exist_ok=True)
    VERSION_JSON.write_text(json.dumps(info, indent=2) + "\n")
    try:
        display = VERSION_JSON.relative_to(REPO_ROOT)
    except ValueError:
        display = VERSION_JSON
    print(f"Wrote {display}: {info['version_string']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
