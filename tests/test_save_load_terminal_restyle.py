"""Tests for save/load modal terminal restyling (issue #137)."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


def _read(filename):
    path = os.path.join(GAME_DIR, filename)
    with open(path) as f:
        return f.read()


# ── Box-drawing border ──


def test_ui_js_has_box_border_builder():
    """ui.js builds box-drawing borders for the modal."""
    content = _read("ui.js")
    assert "buildBoxBorder" in content, "Missing buildBoxBorder function"


def test_ui_js_uses_box_drawing_chars():
    """ui.js uses box-drawing characters for the modal frame."""
    content = _read("ui.js")
    # Top corners and horizontal bar
    assert "\\u2554" in content, "Missing top-left corner (╔)"
    assert "\\u2550" in content, "Missing horizontal bar (═)"
    assert "\\u2557" in content, "Missing top-right corner (╗)"
    # Bottom corners
    assert "\\u255A" in content, "Missing bottom-left corner (╚)"
    assert "\\u255D" in content, "Missing bottom-right corner (╝)"


def test_ui_js_modal_has_border_elements():
    """Modal creates top and bottom border elements."""
    content = _read("ui.js")
    assert "save-load-border-top" in content, "Missing top border element"
    assert "save-load-border-bottom" in content, "Missing bottom border element"


def test_ui_css_has_border_styles():
    """CSS styles the box-drawing border elements."""
    content = _read("ui.css")
    assert ".save-load-border-top" in content, "Missing border-top CSS"
    assert ".save-load-border-bottom" in content, "Missing border-bottom CSS"


# ── Bilingual slot labels ──


def test_ui_js_has_bilingual_slot_labels():
    """Slot labels include both English and Russian text."""
    content = _read("ui.js")
    assert "SLOT_LABELS" in content, "Missing SLOT_LABELS map"
    # Check for Cyrillic СЛОТ via unicode escapes or literal
    assert "\\u0421\\u041B\\u041E\\u0422" in content or "\u0421\u041B\u041E\u0422" in content, (
        "Missing Russian СЛОТ label"
    )


def test_ui_js_has_bilingual_auto_label():
    """Auto-save label includes Russian translation."""
    content = _read("ui.js")
    # АВТО (AUTO in Russian) via unicode escapes or literal
    assert "\\u0410\\u0412\\u0422\\u041E" in content or "\u0410\u0412\u0422\u041E" in content, (
        "Missing Russian АВТО label"
    )


def test_ui_js_has_bilingual_title():
    """Modal title includes bilingual text (English / Russian)."""
    content = _read("ui.js")
    # СОХРАНИТЬ (SAVE) via escapes or literal
    assert "\\u0421\\u041E\\u0425\\u0420\\u0410\\u041D\\u0418\\u0422\\u042C" in content or "\u0421\u041E\u0425\u0420\u0410\u041D\u0418\u0422\u042C" in content, (
        "Missing Russian СОХРАНИТЬ in save title"
    )
    # ЗАГРУЗИТЬ (LOAD) via escapes or literal
    assert "\\u0417\\u0410\\u0413\\u0420\\u0423\\u0417\\u0418\\u0422\\u042C" in content or "\u0417\u0410\u0413\u0420\u0423\u0417\u0418\u0422\u042C" in content, (
        "Missing Russian ЗАГРУЗИТЬ in load title"
    )


# ── Terminal button styling ──


def test_ui_css_buttons_use_phosphor_colors():
    """Save slot buttons use phosphor color variables."""
    content = _read("ui.css")
    # Check that .save-slot-btn uses phosphor vars
    btn_match = re.search(
        r"\.save-slot-btn\s*\{[^}]+\}", content, re.DOTALL
    )
    assert btn_match, "Missing .save-slot-btn styles"
    btn_css = btn_match.group(0)
    assert "--phosphor" in btn_css, "Buttons should use phosphor color variables"


def test_ui_css_buttons_have_letter_spacing():
    """Terminal buttons have letter-spacing for terminal aesthetic."""
    content = _read("ui.css")
    btn_match = re.search(
        r"\.save-slot-btn\s*\{[^}]+\}", content, re.DOTALL
    )
    assert btn_match, "Missing .save-slot-btn styles"
    btn_css = btn_match.group(0)
    assert "letter-spacing" in btn_css, "Buttons should have letter-spacing"
    assert "text-transform: uppercase" in btn_css, (
        "Buttons should be uppercase"
    )


def test_ui_css_buttons_have_phosphor_hover():
    """Buttons glow with phosphor effect on hover."""
    content = _read("ui.css")
    hover_match = re.search(
        r"\.save-slot-btn:hover\s*\{[^}]+\}", content, re.DOTALL
    )
    assert hover_match, "Missing .save-slot-btn:hover styles"
    hover_css = hover_match.group(0)
    assert "--phosphor" in hover_css, (
        "Hover state should use phosphor color variables"
    )


def test_ui_css_close_button_terminal_style():
    """Close/cancel button matches terminal button style."""
    content = _read("ui.css")
    close_match = re.search(
        r"#save-load-close\s*\{[^}]+\}", content, re.DOTALL
    )
    assert close_match, "Missing #save-load-close styles"
    close_css = close_match.group(0)
    assert "letter-spacing" in close_css, "Close button should have letter-spacing"
    assert "text-transform: uppercase" in close_css, (
        "Close button should be uppercase"
    )


# ── Modal uses phosphor / terminal palette ──


def test_ui_css_modal_uses_phosphor_palette():
    """Modal background and text use phosphor/terminal colors."""
    content = _read("ui.css")
    modal_match = re.search(
        r"#save-load-modal\s*\{[^}]+\}", content, re.DOTALL
    )
    assert modal_match, "Missing #save-load-modal styles"
    modal_css = modal_match.group(0)
    assert "--phosphor" in modal_css, (
        "Modal should use phosphor color variables"
    )
    assert "--screen-bg" in modal_css, (
        "Modal background should use screen-bg"
    )


def test_ui_css_modal_no_border_radius():
    """Terminal modal should not have border-radius (sharp corners)."""
    content = _read("ui.css")
    modal_match = re.search(
        r"#save-load-modal\s*\{[^}]+\}", content, re.DOTALL
    )
    assert modal_match, "Missing #save-load-modal styles"
    modal_css = modal_match.group(0)
    assert "border-radius: 0" in modal_css, (
        "Terminal modal should have no border-radius"
    )


# ── Esc key closes modal ──


def test_ui_js_escape_closes_modal():
    """Pressing Escape closes the save/load modal."""
    content = _read("ui.js")
    # Check that the Escape handler checks _saveLoadModalOpen
    assert "_saveLoadModalOpen" in content, "Missing modal open state flag"
    # The Escape handler should call closeSaveLoadModal when modal is open
    esc_section = content[content.index('e.key === "Escape"'):]
    esc_section = esc_section[:500]
    assert "closeSaveLoadModal" in esc_section, (
        "Escape handler should close the save/load modal"
    )
    assert "_saveLoadModalOpen" in esc_section, (
        "Escape handler should check if modal is open"
    )


# ── IBM Plex Mono usage ──


def test_ui_css_modal_uses_ibm_plex_mono():
    """Modal and its elements use IBM Plex Mono font."""
    content = _read("ui.css")
    modal_match = re.search(
        r"#save-load-modal\s*\{[^}]+\}", content, re.DOTALL
    )
    assert modal_match, "Missing #save-load-modal styles"
    modal_css = modal_match.group(0)
    assert "IBM Plex Mono" in modal_css, (
        "Modal should use IBM Plex Mono font"
    )


# ── Cancel button text ──


def test_ui_js_cancel_button_text():
    """Close button uses CANCEL label for terminal consistency."""
    content = _read("ui.js")
    # Look for the close button text near save-load-close
    close_section = content[content.index('"save-load-close"'):]
    close_section = close_section[:200]
    assert "CANCEL" in close_section, (
        "Close button should be labeled CANCEL"
    )
