"""Tests for the web UI shell (issue #13, updated for #132 terminal port)."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── HTML structure tests ──


def test_play_html_exists():
    """play.html exists in the game directory."""
    path = os.path.join(GAME_DIR, "play.html")
    assert os.path.isfile(path), "game/play.html not found"


def test_play_html_has_doctype():
    """play.html starts with a DOCTYPE declaration."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert content.strip().startswith("<!DOCTYPE html>"), "Missing DOCTYPE"


def test_play_html_has_game_title():
    """play.html references the game title MIR'S END."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert "MIR'S END" in content or "MIR&#39;S END" in content, (
        "Game title not in play.html"
    )


def test_play_html_has_terminal_layout():
    """play.html contains the Soviet terminal bezel + screen structure."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    # Terminal bezel
    assert 'id="terminal"' in content, "Missing terminal bezel"
    # Phosphor screen
    assert 'id="screen"' in content, "Missing screen element"
    # Pre-based display
    assert 'id="display"' in content, "Missing display <pre>"
    # Hidden story-output (for session recording + e2e compat)
    assert 'id="story-output"' in content, "Missing story output div"
    # Command input
    assert 'id="command-input"' in content, "Missing command input"


def test_play_html_has_bezel_chrome():
    """play.html includes bezel plate, power LED, brand stamp."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="bezel-plate"' in content, "Missing bezel plate"
    assert 'id="power-led"' in content, "Missing power LED"
    assert 'id="brand"' in content, "Missing brand stamp"
    assert "ЭЛЕКТРОНИКА" in content, "Missing Cyrillic brand text"


def test_play_html_has_save_load_buttons():
    """play.html retains save/load/export buttons for runtime hooks."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="btn-save"' in content, "Missing save button"
    assert 'id="btn-load"' in content, "Missing load button"
    assert 'id="btn-continue"' in content, "Missing continue button"
    assert 'id="btn-export"' in content, "Missing export button"


def test_play_html_has_interpreter_config():
    """play.html includes interpreter configuration for the story file."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert "dist/story.ulx" in content, "Missing story file reference"
    assert "parchment_options" in content, "Missing parchment options"


def test_play_html_loads_ui_js():
    """play.html includes the ui.js script."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert "ui.js" in content, "play.html does not reference ui.js"


def test_play_html_loads_ui_css():
    """play.html includes the ui.css stylesheet."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert "ui.css" in content, "play.html does not reference ui.css"


def test_play_html_has_gameport():
    """play.html retains a gameport div for interpreter attachment."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="gameport"' in content, "Missing gameport div for interpreter"


# ── CSS tests ──


def test_ui_css_exists():
    """ui.css stylesheet exists in the game directory."""
    path = os.path.join(GAME_DIR, "ui.css")
    assert os.path.isfile(path), "game/ui.css not found"


def test_ui_css_has_dark_theme():
    """CSS defines a dark background theme."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "--bg-dark" in content, "Missing dark background variable"
    assert "#0a0c10" in content, "No dark background color"


def test_ui_css_has_grid_layout():
    """CSS uses grid layout for the terminal bezel."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "display: grid" in content or "display:grid" in content, (
        "Missing grid layout"
    )
    assert "grid-template-rows" in content, "Missing grid rows definition"


def test_ui_css_has_phosphor_palette():
    """CSS defines the phosphor green color palette."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "--phosphor:" in content, "Missing phosphor color variable"
    assert "--phosphor-dim:" in content, "Missing phosphor-dim variable"
    assert "--phosphor-bright:" in content, "Missing phosphor-bright variable"
    assert "--lamp-red:" in content, "Missing lamp-red variable"
    assert "--lamp-amber:" in content, "Missing lamp-amber variable"
    assert "--lamp-green:" in content, "Missing lamp-green variable"


def test_ui_css_has_status_colors():
    """CSS defines status indicator colors (green/yellow/red)."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "--status-green" in content, "Missing green status color"
    assert "--status-yellow" in content, "Missing yellow status color"
    assert "--status-red" in content, "Missing red status color"


def test_ui_css_has_monospace_font():
    """CSS uses monospace font family."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "monospace" in content, "Missing monospace font"


def test_ui_css_has_ibm_plex_mono():
    """CSS loads IBM Plex Mono via @font-face (self-hosted)."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "@font-face" in content, "Missing @font-face declarations"
    assert "IBM Plex Mono" in content, "Missing IBM Plex Mono font family"
    assert "assets/fonts/" in content, "Fonts should be self-hosted in assets/fonts/"


def test_ui_css_styles_scrollbar():
    """CSS customizes the scrollbar."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "scrollbar" in content, "Missing scrollbar styling"


# ── JavaScript tests ──


def test_ui_js_exists():
    """ui.js script exists in the game directory."""
    path = os.path.join(GAME_DIR, "ui.js")
    assert os.path.isfile(path), "game/ui.js not found"


def test_ui_js_has_room_art_mapping():
    """JavaScript maps room names to ASCII art file paths."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "ROOM_ART" in content, "Missing room-to-art mapping"
    assert "crew quarters" in content.lower(), "Missing crew quarters mapping"
    assert "main corridor" in content.lower(), "Missing main corridor mapping"
    assert "command module" in content.lower(), "Missing command module mapping"
    assert "observation cupola" in content.lower(), (
        "Missing observation cupola mapping"
    )


def test_ui_js_references_ascii_assets():
    """JavaScript references the correct ASCII art file paths."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    expected_assets = [
        "assets/ascii/bunks.txt",
        "assets/ascii/corridor.txt",
        "assets/ascii/command_module.txt",
        "assets/ascii/darkness.txt",
    ]
    for asset in expected_assets:
        assert asset in content, f"Missing asset reference: {asset}"


def test_ui_js_has_command_history():
    """JavaScript implements command history functionality."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "commandHistory" in content, "Missing command history array"
    assert "ArrowUp" in content, "Missing up-arrow key handler"
    assert "ArrowDown" in content, "Missing down-arrow key handler"
    assert "historyIndex" in content, "Missing history index tracking"


def test_ui_js_has_status_update():
    """JavaScript includes status panel update logic."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "updateStatus" in content, "Missing updateStatus function"
    assert "state.o2" in content or "o2" in content, "Missing O2 state tracking"
    assert "state.morale" in content or "morale" in content, (
        "Missing morale state tracking"
    )
    assert "inventory" in content, "Missing inventory tracking"


def test_ui_js_has_room_detection():
    """JavaScript detects room changes from story text."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "detectRoomChange" in content, "Missing room change detection"
    assert "KNOWN_ROOMS" in content, "Missing known rooms list"


def test_ui_js_has_interpreter_hooks():
    """JavaScript includes hooks for Quixe and Parchment interpreters."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "hookInterpreter" in content, "Missing interpreter hook function"
    assert "GlkOte" in content, "Missing GlkOte/Quixe integration"
    assert "parchment" in content.lower(), "Missing Parchment integration"


def test_ui_js_has_public_api():
    """JavaScript exposes a public API for interpreter integration."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "window.MirsEnd" in content, "Missing public API"
    assert "appendStoryText" in content, "Missing appendStoryText in API"
    assert "setState" in content, "Missing setState in API"


def test_ui_js_has_scene_art_loading():
    """JavaScript loads scene art via fetch."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "loadSceneArt" in content, "Missing scene art loading function"
    assert "fetch(" in content, "Missing fetch call for art loading"
    assert "artCache" in content, "Missing art cache"


def test_ui_js_has_input_handling():
    """JavaScript handles text input and sends to interpreter."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "handleKeyDown" in content, "Missing key handler"
    assert "sendToInterpreter" in content, "Missing interpreter send function"
    assert "Enter" in content, "Missing Enter key handling"


# ── CRT input polish (issue #133) ──


def test_ui_js_input_line_uses_bri_phosphor():
    """The composed input line wraps the typed text in <bri> so it
    renders in bright phosphor — the polish in #133."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    # The prompt `>` and the typed input share one <bri> wrapper, and
    # the blinking cursor immediately follows. This is the literal token
    # the renderer pushes into the bottom row of the box-drawing frame.
    assert "<bri>&gt; ${inputText}</bri><cur>" in content, (
        "Input line should wrap typed text in <bri> phosphor"
    )


def test_ui_js_persists_command_history():
    """Command history persists across page reloads via localStorage."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "mirsend_command_history" in content, (
        "Missing dedicated localStorage key for command history"
    )
    assert "loadCommandHistory" in content, "Missing history loader"
    assert "persistCommandHistory" in content, "Missing history persister"


def test_ui_css_input_box_is_inside_box_drawing_frame():
    """The visible input row is part of the <pre id='display'> grid
    inside the screen, not a free-floating textbox."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        html = f.read()
    # The actual <input> is fixed-positioned with opacity:0 — it only
    # captures keystrokes. The visible prompt is drawn into the grid.
    assert 'id="command-input"' in html, "Missing capture input"
    assert "opacity:0" in html, "Capture input should be transparent"
    assert 'id="display"' in html, "Missing display <pre> where the grid renders"


def test_ui_js_has_compose_function():
    """JavaScript has compose() for building the 80x25 grid."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "function compose" in content, "Missing compose function"
    assert "TOTAL_W" in content, "Missing TOTAL_W grid constant"
    assert "STORY_W" in content, "Missing STORY_W grid constant"
    assert "SIDE_W" in content, "Missing SIDE_W grid constant"


def test_ui_js_has_word_wrap():
    """JavaScript word-wraps story text at STORY_W (48 chars)."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "wordWrap" in content, "Missing wordWrap function"


# ── Integration tests ──


def test_ascii_assets_match_room_mapping():
    """All ASCII art files referenced in the room mapping exist."""
    asset_files = [
        "bunks.txt",
        "corridor.txt",
        "command_module.txt",
        "earth_from_orbit.txt",
        "darkness.txt",
    ]
    ascii_dir = os.path.join(GAME_DIR, "assets", "ascii")
    for filename in asset_files:
        path = os.path.join(ascii_dir, filename)
        assert os.path.isfile(path), f"Missing ASCII art asset: {filename}"


def test_all_files_are_valid_utf8():
    """All UI files are valid UTF-8."""
    ui_files = ["play.html", "ui.css", "ui.js"]
    for filename in ui_files:
        path = os.path.join(GAME_DIR, filename)
        with open(path, encoding="utf-8") as f:
            try:
                f.read()
            except UnicodeDecodeError:
                raise AssertionError(f"{filename} is not valid UTF-8")


def test_font_files_exist():
    """Self-hosted IBM Plex Mono woff2 files exist."""
    fonts_dir = os.path.join(GAME_DIR, "assets", "fonts")
    assert os.path.isdir(fonts_dir), "Missing fonts directory"
    woff2_files = [f for f in os.listdir(fonts_dir) if f.endswith(".woff2")]
    assert len(woff2_files) >= 4, (
        f"Expected at least 4 woff2 font files, found {len(woff2_files)}"
    )
