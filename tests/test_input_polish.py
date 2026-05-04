"""Tests for CRT input polish: phosphor text, blinking cursor, dim echo,
command history persistence, and box-frame integration (issue #133)."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── Phosphor bright input styling ──


def test_css_defines_phosphor_variables():
    """ui.css declares --phosphor-bright and --phosphor-glow variables."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "--phosphor-bright" in content, "Missing --phosphor-bright CSS variable"
    assert "--phosphor-glow" in content, "Missing --phosphor-glow CSS variable"


def test_input_uses_phosphor_color():
    """#command-input color references the phosphor-bright variable."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    # Find the #command-input rule block
    assert "var(--phosphor-bright)" in content, (
        "Input should use phosphor-bright color"
    )


def test_input_has_glow_text_shadow():
    """#command-input has a text-shadow for the phosphor glow effect."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "var(--phosphor-glow)" in content, (
        "Input should have phosphor glow text-shadow"
    )


# ── Blinking block cursor ──


def test_html_has_cursor_element():
    """play.html contains a #input-cursor span for the blinking block cursor."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="input-cursor"' in content, "Missing #input-cursor element"
    # Should contain the █ character (U+2588)
    assert "\u2588" in content or "&#x2588;" in content, (
        "Cursor element should contain block character"
    )


def test_css_has_cursor_blink_animation():
    """ui.css defines a blink animation for the cursor."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "blink-cursor" in content, "Missing blink-cursor animation"
    assert "@keyframes blink-cursor" in content, (
        "Missing @keyframes blink-cursor definition"
    )


def test_css_hides_native_caret():
    """#command-input hides the native browser caret."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "caret-color: transparent" in content, (
        "Native caret should be hidden with caret-color: transparent"
    )


def test_css_cursor_element_styled():
    """#input-cursor has phosphor color and animation."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "#input-cursor" in content, "Missing #input-cursor CSS rule"
    assert "animation:" in content or "animation: blink-cursor" in content, (
        "Cursor should have blink animation"
    )


# ── Dim command echo ──


def test_player_input_echo_is_dim():
    """Player input in story output uses dim styling, not bold."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    # Extract the .player-input rule
    assert "var(--text-dim)" in content, (
        "Player input echo should use dim text color"
    )


def test_js_echo_has_echo_class():
    """appendPlayerInput adds 'echo' class for dim echo styling."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert '"player-input echo"' in content or "'player-input echo'" in content, (
        "Echo span should include 'echo' CSS class"
    )


# ── Command history persistence ──


def test_js_has_history_persistence_key():
    """ui.js defines a localStorage key for command history."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "HISTORY_KEY" in content, "Missing HISTORY_KEY constant"
    assert "mirsend_cmd_history" in content, (
        "History key should be 'mirsend_cmd_history'"
    )


def test_js_has_persist_history_function():
    """ui.js has a persistHistory function that writes to localStorage."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "persistHistory" in content, "Missing persistHistory function"
    assert "localStorage.setItem(HISTORY_KEY" in content, (
        "persistHistory should write to localStorage with HISTORY_KEY"
    )


def test_js_has_restore_history_function():
    """ui.js has a restoreHistory function that reads from localStorage."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "restoreHistory" in content, "Missing restoreHistory function"
    assert "localStorage.getItem(HISTORY_KEY)" in content, (
        "restoreHistory should read from localStorage with HISTORY_KEY"
    )


def test_js_calls_restore_history_on_init():
    """restoreHistory is called during initialization."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "restoreHistory()" in content, (
        "restoreHistory should be called during init"
    )


def test_js_calls_persist_history_on_command():
    """persistHistory is called after a command is entered."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    # persistHistory should appear in the Enter key handler block
    assert "persistHistory()" in content, (
        "persistHistory should be called after command entry"
    )


# ── Up/down arrow history (pre-existing, verify still intact) ──


def test_js_up_down_history_still_works():
    """Arrow key handlers for command history are still present."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "ArrowUp" in content, "Missing ArrowUp handler"
    assert "ArrowDown" in content, "Missing ArrowDown handler"
    assert "historyIndex" in content, "Missing historyIndex tracking"


# ── Input bar frame integration ──


def test_input_bar_uses_panel_background():
    """Input bar background matches panel bg for frame integration."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    # The input bar should use the panel background, not a distinct input bg
    assert re.search(
        r"#input-bar\s*\{[^}]*var\(--bg-panel\)", content
    ), "Input bar should use --bg-panel for frame integration"


def test_input_bar_in_html_has_frame_comment():
    """play.html input bar section mentions box-drawing frame integration."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert "box-drawing frame" in content.lower() or "frame" in content.lower(), (
        "Input bar HTML should reference frame integration"
    )
