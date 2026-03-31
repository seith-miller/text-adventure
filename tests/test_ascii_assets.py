"""Tests for placeholder ASCII art assets."""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASCII_DIR = os.path.join(ROOT, "game", "assets", "ascii")

EXPECTED_FILES = [
    "darkness.txt",
    "corridor.txt",
    "bunks.txt",
    "command_module.txt",
    "radio.txt",
    "earth_burning.txt",
    "earth_from_orbit.txt",
]

MAX_WIDTH = 80
MAX_HEIGHT = 40


def test_all_ascii_files_exist():
    for filename in EXPECTED_FILES:
        path = os.path.join(ASCII_DIR, filename)
        assert os.path.isfile(path), f"Missing ASCII art file: {filename}"


def test_files_within_80x40_bounds():
    for filename in EXPECTED_FILES:
        path = os.path.join(ASCII_DIR, filename)
        with open(path) as f:
            lines = f.readlines()
        # Strip trailing newline from line count
        content_lines = [l.rstrip("\n") for l in lines]
        # Remove trailing empty lines for height check
        while content_lines and content_lines[-1] == "":
            content_lines.pop()
        assert len(content_lines) <= MAX_HEIGHT, (
            f"{filename} is {len(content_lines)} lines tall (max {MAX_HEIGHT})"
        )
        for i, line in enumerate(content_lines):
            assert len(line) <= MAX_WIDTH, (
                f"{filename} line {i+1} is {len(line)} chars wide (max {MAX_WIDTH})"
            )


def test_files_contain_recognizable_content():
    """Each file should have non-trivial content, not just whitespace."""
    for filename in EXPECTED_FILES:
        path = os.path.join(ASCII_DIR, filename)
        with open(path) as f:
            content = f.read()
        non_whitespace = content.replace(" ", "").replace("\n", "").replace("\t", "")
        assert len(non_whitespace) > 5, (
            f"{filename} has too little content ({len(non_whitespace)} non-whitespace chars)"
        )


def test_files_use_only_printable_ascii():
    for filename in EXPECTED_FILES:
        path = os.path.join(ASCII_DIR, filename)
        with open(path) as f:
            content = f.read()
        for i, ch in enumerate(content):
            assert ch == "\n" or (32 <= ord(ch) <= 126), (
                f"{filename} contains non-printable/non-ASCII char "
                f"ord={ord(ch)} at position {i}"
            )
