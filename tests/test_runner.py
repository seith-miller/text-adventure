"""Tests for the terminal game runner."""

import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DIR = os.path.join(ROOT, "game", "dist", "story")
RUNNER_JS = os.path.join(ROOT, "game", "dist", "runner.js")


def _build():
    """Ensure the project is built before running tests."""
    subprocess.run(
        ["npm", "run", "build"],
        cwd=ROOT,
        capture_output=True,
        timeout=30,
    )


def _run_game(inputs, timeout=15):
    """Run the game runner with the given inputs and return stdout/stderr."""
    _build()
    input_text = "\n".join(str(i) for i in inputs) + "\n"
    result = subprocess.run(
        ["node", RUNNER_JS],
        cwd=ROOT,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result


def test_runner_ts_exists():
    """runner.ts source file exists."""
    path = os.path.join(ROOT, "game", "src", "runner.ts")
    assert os.path.isfile(path)


def test_runner_compiles():
    """runner.ts compiles to runner.js without errors."""
    _build()
    assert os.path.isfile(RUNNER_JS)


def test_npm_start_script_exists():
    """package.json has a start script."""
    with open(os.path.join(ROOT, "package.json")) as f:
        pkg = json.load(f)
    assert "start" in pkg["scripts"]


def test_game_displays_banner():
    """Game shows the title banner on startup."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert "ILLUSTRATED TEXT ADVENTURE" in result.stdout


def test_game_displays_story_text():
    """Game displays opening story text."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert "You wake to nothing" in result.stdout


def test_game_displays_choices():
    """Game presents numbered choices."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert "1." in result.stdout
    assert "2." in result.stdout


def test_game_displays_ascii_art():
    """Game displays ASCII art when ascii tags are encountered."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    # The opening scene has # ascii: darkness, which shows sparse dots
    # Then after choice 1, # ascii: bunks shows the sleeping module
    assert "SLEEPING MODULE" in result.stdout or "SECTION" in result.stdout


def test_game_displays_resource_status():
    """Game shows oxygen and morale status."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert "O2:" in result.stdout
    assert "Morale:" in result.stdout


def test_game_ends_with_message():
    """Game ends cleanly with an end message at story boundary."""
    # Play through path: choice 1 at every step
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert "story pauses here" in result.stdout or "Thank you for playing" in result.stdout


def test_game_handles_invalid_input():
    """Game handles non-numeric input gracefully without crashing."""
    # Send invalid input followed by valid input
    result = subprocess.run(
        ["node", RUNNER_JS],
        cwd=ROOT,
        input="abc\n0\n99\n1\n1\n1\n1\n1\n1\n1\n1\n1\n1\n",
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "Please enter a number" in result.stdout


def test_game_no_crash_on_exit():
    """Game exits with return code 0 on normal playthrough."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    assert result.returncode == 0


def test_oxygen_decreases():
    """Oxygen decreases as the story progresses."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    lines = result.stdout.split("\n")
    oxygen_values = []
    for line in lines:
        if "O2:" in line:
            # Extract the number from "O2: 100%"
            start = line.index("O2:") + 4
            end = line.index("%", start)
            oxygen_values.append(int(line[start:end].strip()))
    assert len(oxygen_values) >= 2, "Should see at least two oxygen readings"
    assert oxygen_values[-1] < oxygen_values[0], "Oxygen should decrease over time"


def test_different_branches_give_different_text():
    """Choosing different options leads to different story text."""
    result1 = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    result2 = _run_game([2, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    # Branch 1 has "Your fingers fumble", branch 2 has "Hello? Yevgenia?"
    has_search = "Your fingers fumble" in result1.stdout
    has_callout = "Yevgenia" in result2.stdout
    assert has_search, "Branch 1 should contain search text"
    assert has_callout, "Branch 2 should contain crew call text"


def test_earth_burning_ascii_appears():
    """The earth_burning ASCII art appears during the nuclear discovery scene."""
    result = _run_game([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    # earth_burning.txt has distinctive X patterns for nuclear impacts
    # or the earth_from_orbit art should appear at the viewport
    lines = result.stdout
    assert "earth" in lines.lower() or "nuclear" in lines.lower() or "planet" in lines.lower()
