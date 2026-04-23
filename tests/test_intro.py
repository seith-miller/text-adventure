"""Tests for the intro sequence (issue #16)."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── File existence ──


def test_intro_js_exists():
    """intro.js exists in the game directory."""
    path = os.path.join(GAME_DIR, "intro.js")
    assert os.path.isfile(path), "game/intro.js not found"


def test_intro_css_exists():
    """intro.css exists in the game directory."""
    path = os.path.join(GAME_DIR, "intro.css")
    assert os.path.isfile(path), "game/intro.css not found"


# ── HTML integration ──


def test_play_html_loads_intro_js():
    """play.html includes the intro.js script."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'src="intro.js"' in content, "intro.js not referenced in play.html"


def test_play_html_loads_intro_css():
    """play.html includes the intro.css stylesheet."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'href="intro.css"' in content, "intro.css not referenced in play.html"


def test_intro_js_loads_before_ui_js():
    """intro.js is loaded before ui.js so the API is available."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    intro_pos = content.find('src="intro.js"')
    ui_pos = content.find('src="ui.js"')
    assert intro_pos != -1, "intro.js not found in play.html"
    assert ui_pos != -1, "ui.js not found in play.html"
    assert intro_pos < ui_pos, "intro.js must load before ui.js"


# ── Intro sequence content ──


def test_intro_has_datestamp():
    """Intro sequence includes a Cold War era date/time stamp."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "1988" in content, "Missing Cold War era date"
    assert "MSK" in content, "Missing Moscow time reference"


def test_intro_has_station_reference():
    """Intro references the space station."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "MIR" in content or "station" in content.lower(), (
        "Missing station reference in intro"
    )
    assert "orbit" in content.lower(), "Missing orbital reference in intro"


def test_intro_has_emp_flash():
    """Intro includes an EMP flash event."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "flash" in content.lower(), "Missing flash event in intro"


def test_intro_css_has_flash_animation():
    """Intro CSS defines the EMP flash animation."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert "emp-flash" in content, "Missing emp-flash keyframes"
    assert "@keyframes" in content, "Missing animation keyframes"


def test_intro_has_title_reveal():
    """Intro ends with the game title reveal."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    # The title should appear in one of the steps
    assert "MIR" in content and "END" in content, "Missing title in intro"
    assert "intro-title" in content, "Missing title styling class"


# ── Skippable ──


def test_intro_is_skippable_by_key():
    """Intro registers a keydown listener for skipping."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "keydown" in content, "Missing keydown listener for skip"
    assert "handleSkip" in content or "skip" in content.lower(), (
        "Missing skip handler"
    )


def test_intro_is_skippable_by_click():
    """Intro registers a click listener for skipping."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "click" in content, "Missing click listener for skip"


def test_intro_has_skip_prompt():
    """Intro displays a skip prompt to the user."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "skip" in content.lower(), "Missing skip prompt text"


def test_intro_css_has_skip_styling():
    """CSS includes styling for the skip prompt."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert "intro-skip" in content, "Missing skip prompt styling"


# ── No replay on Continue/Load ──


def test_intro_uses_session_storage():
    """Intro uses sessionStorage to track whether it has played."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "sessionStorage" in content, "Missing sessionStorage usage"


def test_intro_checks_skip_params():
    """Intro checks URL params for skip/continue/load markers."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "skip_intro" in content, "Missing skip_intro URL param check"
    assert "continue" in content, "Missing continue param check"
    assert "load" in content, "Missing load param check"


def test_intro_does_not_replay():
    """shouldPlayIntro checks storage before running."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "shouldPlayIntro" in content, "Missing shouldPlayIntro function"
    # The run function should call shouldPlayIntro
    assert re.search(
        r"shouldPlayIntro\s*\(\s*\)", content
    ), "run() must check shouldPlayIntro()"


# ── Smooth transition into game ──


def test_intro_transitions_to_game():
    """Intro ends by showing the game shell and calling a completion callback."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "game-shell" in content, "Missing game-shell reference for transition"
    assert "onCompleteCallback" in content or "callback" in content, (
        "Missing completion callback"
    )


def test_intro_overlay_fades_out():
    """Intro overlay fades out rather than disappearing abruptly."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "opacity" in content, "Missing opacity transition for fade-out"


def test_ui_js_integrates_intro():
    """ui.js init() checks for MirsEndIntro and runs it."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "MirsEndIntro" in content, "ui.js does not reference MirsEndIntro"
    assert "MirsEndIntro.run" in content, "ui.js does not call MirsEndIntro.run"


# ── Intro CSS structure ──


def test_intro_overlay_is_fullscreen():
    """Intro overlay covers the full viewport."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert "position: fixed" in content, "Overlay must be fixed position"
    assert "width: 100%" in content, "Overlay must cover full width"
    assert "height: 100%" in content, "Overlay must cover full height"
    assert "z-index" in content, "Overlay must have z-index"


def test_intro_has_text_styling():
    """Intro CSS defines distinct styles for different text types."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert ".intro-datestamp" in content, "Missing datestamp style"
    assert ".intro-narrative" in content, "Missing narrative style"
    assert ".intro-title" in content, "Missing title style"


def test_intro_has_fade_transitions():
    """Intro text lines use opacity transitions for smooth reveal."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert ".intro-line" in content, "Missing intro-line class"
    assert "opacity" in content, "Missing opacity transitions"
    assert ".visible" in content or ".fade-out" in content, (
        "Missing visibility state classes"
    )


# ── Public API ──


def test_intro_exposes_public_api():
    """Intro exposes a window.MirsEndIntro public API."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "window.MirsEndIntro" in content, "Missing public API"
    assert "shouldPlayIntro" in content, "API missing shouldPlayIntro"
    assert "run" in content, "API missing run method"
    assert "skip" in content, "API missing skip method"
    assert "isActive" in content, "API missing isActive method"


# ── Timing ──


def test_intro_duration_under_60_seconds():
    """Intro sequence completes within 60 seconds."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    # Extract all delay values from INTRO_STEPS
    delays = [int(d) for d in re.findall(r"delay:\s*(\d+)", content)]
    assert len(delays) > 0, "No delays found in INTRO_STEPS"
    max_delay = max(delays)
    assert max_delay <= 60000, (
        f"Intro max delay {max_delay}ms exceeds 60 seconds"
    )


def test_intro_has_multiple_steps():
    """Intro has a meaningful number of sequence steps."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    delays = re.findall(r"delay:\s*\d+", content)
    assert len(delays) >= 10, (
        f"Only {len(delays)} steps found — intro should be substantial"
    )
