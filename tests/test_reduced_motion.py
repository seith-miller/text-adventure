"""Tests for the reduced-motion accessibility mode (issue #144)."""

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
    """reduced-motion.js loads before intro.js so the API is available."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    rm_pos = content.find('src="reduced-motion.js"')
    intro_pos = content.find('src="intro.js"')
    assert rm_pos != -1, "reduced-motion.js not found in play.html"
    assert intro_pos != -1, "intro.js not found in play.html"
    assert rm_pos < intro_pos, "reduced-motion.js must load before intro.js"


def test_reduced_motion_loads_before_ui():
    """reduced-motion.js loads before ui.js so the API is available."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    rm_pos = content.find('src="reduced-motion.js"')
    ui_pos = content.find('src="ui.js"')
    assert rm_pos != -1, "reduced-motion.js not found in play.html"
    assert ui_pos != -1, "ui.js not found in play.html"
    assert rm_pos < ui_pos, "reduced-motion.js must load before ui.js"


# ── Public API ──


def test_exposes_public_api():
    """reduced-motion.js exposes window.MirsEndMotion public API."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "window.MirsEndMotion" in content, "Missing public API"
    assert "init" in content, "API missing init method"
    assert "getMode" in content, "API missing getMode method"
    assert "setMode" in content, "API missing setMode method"
    assert "cycleMode" in content, "API missing cycleMode method"
    assert "isReduced" in content, "API missing isReduced method"


# ── OS detection ──


def test_detects_prefers_reduced_motion():
    """Module checks prefers-reduced-motion media query."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "prefers-reduced-motion" in content, (
        "Missing prefers-reduced-motion media query"
    )
    assert "matchMedia" in content, "Missing matchMedia usage"


def test_listens_for_media_query_changes():
    """Module listens for changes to the media query."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "addEventListener" in content, (
        "Missing event listener for media query changes"
    )
    assert '"change"' in content or "'change'" in content, (
        "Missing change event listener"
    )


# ── Three-mode toggle (off / on / auto) ──


def test_supports_three_modes():
    """Module supports auto, on, and off modes."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert '"auto"' in content, "Missing auto mode"
    assert '"on"' in content, "Missing on mode"
    assert '"off"' in content, "Missing off mode"


def test_cycle_mode_rotates_through_modes():
    """cycleMode cycles through auto → on → off → auto."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "cycleMode" in content, "Missing cycleMode function"
    # Should reference VALID_MODES array for cycling
    assert "VALID_MODES" in content, "Missing VALID_MODES reference in cycleMode"


# ── Persistence ──


def test_persists_to_local_storage():
    """Module persists preference to localStorage."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "localStorage" in content, "Missing localStorage usage"
    assert "mirsend_reduced_motion" in content, (
        "Missing localStorage key for reduced motion"
    )


# ── CSS class gating ──


def test_adds_reduced_motion_class():
    """Module adds/removes .reduced-motion class on <html>."""
    path = os.path.join(GAME_DIR, "reduced-motion.js")
    with open(path) as f:
        content = f.read()
    assert "reduced-motion" in content, "Missing reduced-motion class reference"
    assert "classList" in content, "Missing classList manipulation"
    assert "documentElement" in content, (
        "Should target document.documentElement (<html>)"
    )


# ── CSS overrides: intro animations ──


def test_intro_css_disables_flash_animation():
    """Intro CSS disables EMP flash when reduced-motion is active."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert ".reduced-motion" in content, (
        "Missing .reduced-motion overrides in intro.css"
    )
    assert re.search(
        r"\.reduced-motion.*#intro-flash", content, re.DOTALL
    ), "Missing reduced-motion override for #intro-flash"


def test_intro_css_disables_static_flicker():
    """Intro CSS disables scanline flicker but keeps static overlay."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*#intro-static", content, re.DOTALL
    ), "Missing reduced-motion override for #intro-static"
    # Should keep a static opacity rather than hiding completely
    assert "opacity: 0.04" in content, (
        "Static overlay should remain visible at low opacity"
    )


def test_intro_css_hard_cut_text_transitions():
    """Intro CSS uses hard cut (transition: none) for text in reduced mode."""
    path = os.path.join(GAME_DIR, "intro.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*\.intro-line", content, re.DOTALL
    ), "Missing reduced-motion override for .intro-line"
    assert "transition: none" in content, (
        "Missing transition: none for hard cut"
    )


# ── CSS overrides: UI animations ──


def test_ui_css_disables_status_bar_transition():
    """UI CSS disables status bar transitions in reduced-motion mode."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*\.bar-fill", content, re.DOTALL
    ), "Missing reduced-motion override for status bar"


def test_ui_css_disables_button_transitions():
    """UI CSS disables button hover transitions in reduced-motion mode."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert re.search(
        r"\.reduced-motion.*\.menu-btn", content, re.DOTALL
    ), "Missing reduced-motion override for menu buttons"


# ── Settings UI ──


def test_settings_button_is_enabled():
    """Settings button is wired up in ui.js (no longer disabled)."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "menu-settings" in content, (
        "ui.js does not reference #menu-settings button"
    )
    assert "initSettingsButton" in content, (
        "Missing initSettingsButton function"
    )


def test_settings_modal_exists():
    """ui.js creates a settings modal with reduced-motion toggle."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "showSettingsModal" in content, "Missing showSettingsModal function"
    assert "closeSettingsModal" in content, "Missing closeSettingsModal function"
    assert "settings-modal" in content, "Missing settings-modal element"


def test_settings_modal_has_motion_toggle():
    """Settings modal includes a reduced-motion cycle button."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "MirsEndMotion" in content, (
        "Settings UI does not reference MirsEndMotion API"
    )
    assert "cycleMode" in content, "Settings UI does not call cycleMode"


def test_settings_css_exists():
    """ui.css includes settings modal styling."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "#settings-modal" in content, "Missing #settings-modal styles"
    assert "#settings-overlay" in content, "Missing #settings-overlay styles"


# ── Intro.js integration ──


def test_intro_respects_reduced_motion():
    """intro.js checks reduced motion state for flash and transitions."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    assert "isReducedMotion" in content or "MirsEndMotion" in content, (
        "intro.js does not check reduced motion state"
    )


def test_intro_skips_flash_in_reduced_motion():
    """intro.js skips EMP flash when reduced motion is active."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    # triggerFlash should check isReducedMotion
    assert re.search(
        r"triggerFlash.*isReducedMotion", content, re.DOTALL
    ), "triggerFlash should check isReducedMotion"


def test_intro_hard_cut_end_in_reduced_motion():
    """intro.js ends with hard cut (no fade) when reduced motion is active."""
    path = os.path.join(GAME_DIR, "intro.js")
    with open(path) as f:
        content = f.read()
    # endIntro should have a reduced motion branch
    assert re.search(
        r"endIntro.*isReducedMotion", content, re.DOTALL
    ), "endIntro should check isReducedMotion for hard cut"


# ── UI.js integration ──


def test_ui_initializes_reduced_motion():
    """ui.js calls MirsEndMotion.init() during initialization."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "MirsEndMotion.init" in content, (
        "ui.js does not call MirsEndMotion.init()"
    )
