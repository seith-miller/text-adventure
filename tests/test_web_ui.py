"""Tests for the web UI shell (issue #13)."""

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


def test_play_html_has_panel_layout():
    """play.html contains the required panel structure."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    # Left panel — story output
    assert 'id="story-panel"' in content, "Missing story panel"
    assert 'id="story-output"' in content, "Missing story output div"
    # Top right — scene art
    assert 'id="scene-panel"' in content, "Missing scene panel"
    assert 'id="scene-art"' in content, "Missing scene art element"
    # Mid right — title
    assert 'id="title-panel"' in content, "Missing title panel"
    # Bottom right — status
    assert 'id="status-panel"' in content, "Missing status panel"
    # Bottom — input
    assert 'id="input-bar"' in content, "Missing input bar"
    assert 'id="command-input"' in content, "Missing command input"


def test_play_html_has_status_indicators():
    """Status panel includes O2, morale, and inventory elements."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="status-o2"' in content, "Missing O2 status element"
    assert 'id="status-morale"' in content, "Missing morale status element"
    assert 'id="inventory-list"' in content, "Missing inventory list element"


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


def test_play_html_has_sidebar():
    """play.html has a sidebar container for right-side panels."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="sidebar"' in content, "Missing sidebar container"


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
    # Should have dark hex values
    assert "#0a0c10" in content or "#000" in content, "No dark background color"


def test_ui_css_has_grid_layout():
    """CSS uses grid layout for the game shell."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "display: grid" in content or "display:grid" in content, (
        "Missing grid layout"
    )
    assert "grid-template-columns" in content, "Missing grid columns definition"


def test_ui_css_has_blue_scene_styling():
    """CSS includes blue-tinted styling for scene art panel."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "--scene-blue" in content or "--scene-text" in content, (
        "Missing blue scene art styling"
    )


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


def test_ui_css_styles_scrollbar():
    """CSS customizes the scrollbar for the story panel."""
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
    # Check key room mappings
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
