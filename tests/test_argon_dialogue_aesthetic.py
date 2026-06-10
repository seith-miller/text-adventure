"""Tests for Argon-87 dialogue phosphor-native aesthetic (issue #139).

Acceptance criteria:
- Argon speech is visually distinct from narrator prose at a glance
- Reads as native to the terminal aesthetic
- Existing argon-speech CSS hooks still work
- No m8/m9 functional regressions in Argon dialogue tests
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


def _read_ui_css():
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        return f.read()


def _read_station_ai_runtime():
    path = os.path.join(GAME_DIR, "station-ai-runtime.js")
    with open(path) as f:
        return f.read()


# ── CSS hook preservation ──


def test_argon_speech_css_selector_exists():
    """The #story-output .argon-speech selector must still be present."""
    css = _read_ui_css()
    assert "#story-output .argon-speech" in css, (
        "argon-speech CSS hook is missing"
    )


def test_argon_label_css_selector_exists():
    """The #story-output .argon-label selector must still be present."""
    css = _read_ui_css()
    assert "#story-output .argon-label" in css, (
        "argon-label CSS hook is missing"
    )


# ── Phosphor-native visual treatment ──


def test_argon_speech_uses_css_variable_not_hardcoded_gold():
    """Argon speech should use a CSS custom property, not the old hardcoded #c4a35a."""
    css = _read_ui_css()
    # The old gold color should no longer be used for argon-speech
    argon_section = _extract_argon_speech_block(css)
    assert "#c4a35a" not in argon_section, (
        "argon-speech still uses hardcoded gold #c4a35a instead of a CSS variable"
    )


def test_argon_palette_css_variables_defined():
    """CSS root should define Argon-specific palette variables."""
    css = _read_ui_css()
    assert "--argon" in css, (
        "Missing Argon palette CSS variable(s) in :root"
    )


def test_argon_speech_has_text_shadow_glow():
    """Argon speech should have a text-shadow glow to match the phosphor aesthetic."""
    css = _read_ui_css()
    argon_section = _extract_argon_speech_block(css)
    assert "text-shadow" in argon_section, (
        "argon-speech is missing text-shadow glow for phosphor aesthetic"
    )


def test_argon_speech_has_left_border():
    """Argon speech should have a left border for visual distinction."""
    css = _read_ui_css()
    argon_section = _extract_argon_speech_block(css)
    assert "border-left" in argon_section, (
        "argon-speech is missing left border for visual distinction"
    )


# ── Label prefix ──


def test_argon_label_uses_cyrillic_prefix():
    """The JS runtime should render the Cyrillic prefix АРГОН-87."""
    js = _read_station_ai_runtime()
    assert "\u0410\u0420\u0413\u041e\u041d-87" in js, (
        "station-ai-runtime.js should use Cyrillic prefix АРГОН-87"
    )


def test_argon_label_uses_double_colon_separator():
    """The label should use '::' separator in the АРГОН-87 prefix."""
    js = _read_station_ai_runtime()
    assert "\u0410\u0420\u0413\u041e\u041d-87 :: " in js, (
        "station-ai-runtime.js should use 'АРГОН-87 :: ' label text"
    )


# ── Helpers ──


def _extract_argon_speech_block(css):
    """Extract the .argon-speech rule block from CSS text."""
    match = re.search(
        r"#story-output\s+\.argon-speech\s*\{([^}]+)\}", css
    )
    return match.group(1) if match else ""
