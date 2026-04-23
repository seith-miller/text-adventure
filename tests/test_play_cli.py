"""Tests for scripts/play.py, the headless play harness."""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLAY_SCRIPT = REPO_ROOT / "scripts" / "play.py"
STORY = REPO_ROOT / "game" / "dist" / "story.ulx"


needs_glulxe = pytest.mark.skipif(
    shutil.which("glulxe") is None, reason="glulxe not on PATH"
)
needs_story = pytest.mark.skipif(
    not STORY.is_file(), reason="compiled story not built; run `npm run build:story`"
)


@needs_glulxe
@needs_story
def test_play_cli_accepts_newline_commands():
    """Commands on stdin, one per line, produce a JSON transcript."""
    inputs = "open locker\ntake flashlight\nswitch on flashlight\n"
    result = subprocess.run(
        [str(PLAY_SCRIPT)],
        input=inputs,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["turns"] == 3
    assert payload["commands"] == ["open locker", "take flashlight", "switch on flashlight"]
    transcript = payload["transcript"]
    assert "Zhuchok" in transcript or "beetle-drone" in transcript
    assert "Crew Quarters" in transcript


@needs_glulxe
@needs_story
def test_play_cli_accepts_json_commands():
    """--json reads the command array as JSON on stdin."""
    commands = ["open locker", "take flashlight", "switch on flashlight", "pull lever", "n"]
    result = subprocess.run(
        [str(PLAY_SCRIPT), "--json"],
        input=json.dumps(commands),
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["commands"] == commands
    assert "Main Corridor" in payload["transcript"]


@needs_glulxe
@needs_story
def test_play_cli_reports_missing_story():
    """Missing story file exits cleanly with a helpful message."""
    result = subprocess.run(
        [str(PLAY_SCRIPT), "--story", "/tmp/nonexistent.ulx"],
        input="",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr.lower()
