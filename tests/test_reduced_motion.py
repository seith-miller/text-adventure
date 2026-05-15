"""Tests for reduced-motion accessibility mode (issue #144)."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── File existence ──


def test_reduced_motion_js_exists():
    """reduced-motion.js exists in the game directory."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    assert os.path.isfile(path), "game/reduced-motion.js not found"


# ── HTML integration ──


def test_play_html_loads_reduced_motion_js():
    """play.html includes the reduced-motion.js script."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'src="reduced-motion.js"' in content, (
        "reduced-motion.js not referenced in play.html"
    )


def test_reduced_motion_loads_before_intro():
    """reduced-motion.js loads before intro.js so the class is set early."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    motion_pos = content.find('src="reduced-motion.js"')
    intro_pos = content.find('src="intro.js"')
    assert motion_pos != -1, "reduced-motion.js not found in play.html"
    assert intro_pos != -1, "intro.js not found in play.html"
    assert motion_pos < intro_pos, (
        "reduced-motion.js must load before intro.js"
    )


def test_reduced_motion_loads_before_ui():
    """reduced-motion.js loads before ui.js."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    motion_pos = content.find('src="reduced-motion.js"')
    ui_pos = content.find('src="ui.js"')
    assert motion_pos != -1, "reduced-motion.js not found in play.html"
    assert ui_pos != -1, "ui.js not found in play.html"
    assert motion_pos < ui_pos, "reduced-motion.js must load before ui.js"


# ── reduced-motion.js API ──


def test_reduced_motion_exposes_api():
    """reduced-motion.js exposes MirsEndMotion on the window object."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "window.MirsEndMotion" in content, (
        "MirsEndMotion API not exposed"
    )


def test_reduced_motion_has_auto_init():
    """reduced-motion.js auto-initializes on load."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "init()" in content, "init() call not found"


def test_reduced_motion_detects_os_preference():
    """reduced-motion.js queries prefers-reduced-motion media feature."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "prefers-reduced-motion" in content, (
        "OS prefers-reduced-motion detection not implemented"
    )


def test_reduced_motion_supports_three_modes():
    """reduced-motion.js supports auto, on, and off modes."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert '"auto"' in content, "auto mode not found"
    assert '"on"' in content, "on mode not found"
    assert '"off"' in content, "off mode not found"


def test_reduced_motion_persists_to_localstorage():
    """reduced-motion.js uses localStorage for persistence."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "localStorage" in content, "localStorage not used for persistence"
    assert "mirsend_reduced_motion" in content, (
        "Expected storage key not found"
    )


def test_reduced_motion_sets_css_class():
    """reduced-motion.js adds/removes the reduced-motion class on <html>."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert '"reduced-motion"' in content, (
        "reduced-motion class toggle not found"
    )
    assert "classList.add" in content, "classList.add not found"
    assert "classList.remove" in content, "classList.remove not found"


def test_reduced_motion_api_methods():
    """MirsEndMotion API exposes getMode, setMode, cycleMode, isReduced."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    for method in ["getMode", "setMode", "cycleMode", "isReduced"]:
        assert method in content, f"API method {method} not found"


# ── CSS reduced-motion rules ──


def test_ui_css_has_reduced_motion_overrides():
    """ui.css contains .reduced-motion CSS rules to gate animations."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert ".reduced-motion" in content, (
        "No .reduced-motion CSS rules in ui.css"
    )


def test_ui_css_disables_bar_transition():
    """ui.css disables status bar transitions under .reduced-motion."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*\.bar-fill", content, re.DOTALL
    ), "Status bar transition override not found"


def test_intro_css_has_reduced_motion_overrides():
    """intro.css contains .reduced-motion CSS rules for hard cuts."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert ".reduced-motion" in content, (
        "No .reduced-motion CSS rules in intro.css"
    )


def test_intro_css_disables_emp_flash():
    """intro.css disables the EMP flash animation under .reduced-motion."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*#intro-flash", content, re.DOTALL
    ), "EMP flash override not found"


def test_intro_css_disables_static_flicker():
    """intro.css disables static-flicker animation under .reduced-motion."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*#intro-static", content, re.DOTALL
    ), "Static flicker override not found"


def test_intro_css_hard_cuts_intro_lines():
    """intro.css replaces fade transitions with hard cuts under .reduced-motion."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*\.intro-line", content, re.DOTALL
    ), "Intro line hard-cut override not found"


# ── Intro JS reduced-motion awareness ──


def test_intro_js_checks_reduced_motion():
    """intro.js checks reduced-motion state for hard-cut behavior."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "reduced-motion" in content, (
        "intro.js does not check for reduced-motion"
    )


# ── Settings UI ──


def test_settings_button_enabled():
    """Settings button in play.html is not disabled."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    # Find the settings button line
    match = re.search(r'id="menu-settings"[^>]*>', content)
    assert match, "Settings button not found"
    button_tag = match.group(0)
    assert "disabled" not in button_tag, "Settings button should not be disabled"


def test_ui_js_has_settings_modal():
    """ui.js implements a settings modal."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "showSettingsModal" in content, "Settings modal function not found"
    assert "closeSettingsModal" in content, (
        "Settings modal close function not found"
    )


def test_ui_js_settings_has_motion_toggle():
    """ui.js settings modal includes reduced motion toggle."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "MirsEndMotion" in content, (
        "Settings modal does not reference MirsEndMotion"
    )
    assert "cycleMode" in content, (
        "Settings modal does not use cycleMode"
    )


def test_ui_js_exposes_settings_api():
    """MirsEnd API exposes showSettings and closeSettings."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "showSettings" in content, "showSettings not in public API"
    assert "closeSettings" in content, "closeSettings not in public API"


def test_ui_css_has_settings_modal_styles():
    """ui.css includes styles for the settings modal."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "#settings-modal" in content, "Settings modal styles not found"
    assert "#settings-overlay" in content, "Settings overlay styles not found"
