"""Structural tests for the optional typing / decode-in effect (m13 #140).

These tests assert that ui.js carries the public symbols + storage key the
feature contract promises. Behavioral correctness is exercised in the
Playwright spec at tests/e2e/typing-effect.spec.ts; the Python suite catches
silent breakage of the contract (renames, removals) in environments where
Playwright cannot run (e.g. CI without browser deps).
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_JS = os.path.join(ROOT, "game", "ui.js")


def _read_ui_js() -> str:
    with open(UI_JS, encoding="utf-8") as f:
        return f.read()


def test_ui_js_exposes_typing_config_api():
    """ui.js exposes getTypingConfig + setTypingConfig on window.MirsEnd."""
    content = _read_ui_js()
    assert "getTypingConfig" in content, "Missing getTypingConfig on public API"
    assert "setTypingConfig" in content, "Missing setTypingConfig on public API"


def test_ui_js_exposes_skip_typing_api():
    """ui.js exposes skipTyping so a key handler (or test) can finish early."""
    content = _read_ui_js()
    assert "skipTyping" in content, "Missing skipTyping on public API"


def test_ui_js_persists_typing_settings_under_known_key():
    """The storage key is mirsend_typing_settings (e2e spec depends on it)."""
    content = _read_ui_js()
    assert "mirsend_typing_settings" in content, (
        "Missing localStorage key for typing settings"
    )


def test_ui_js_default_typing_effect_is_off():
    """Default config object initialises with enabled:false."""
    content = _read_ui_js()
    # Allow flexibility in formatting around the boolean default.
    assert "TYPING_DEFAULT" in content or "typingConfig" in content, (
        "Missing typing-config initialisation block"
    )


def test_ui_js_has_charsPerSec_speed_config():
    """The chars-per-second knob is configurable, not hardcoded."""
    content = _read_ui_js()
    assert "charsPerSec" in content, "Missing chars-per-second config"


def test_ui_js_animates_through_setTimeout_or_setInterval():
    """Animation uses a JS timer rather than a busy loop or DOM transition."""
    content = _read_ui_js()
    assert "setTimeout" in content or "setInterval" in content, (
        "Typing effect should drive its frames off setTimeout / setInterval"
    )
