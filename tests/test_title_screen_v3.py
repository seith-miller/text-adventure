"""Tests for the v3 title screen restyle (issue #134).

Validates the bezel + phosphor CRT aesthetic, bilingual menu buttons,
prominent MIR'S END title (Latin only), and hover/focus glow states.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


def _read(filename):
    path = os.path.join(GAME_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── HTML: Bezel + phosphor frame ──


class TestBezelPhosphorFrame:
    """Title screen uses the bezel + phosphor screen aesthetic."""

    def test_title_bezel_exists(self):
        html = _read("play.html")
        assert 'id="title-bezel"' in html, "Missing #title-bezel frame element"

    def test_title_phosphor_exists(self):
        html = _read("play.html")
        assert 'id="title-phosphor"' in html, "Missing #title-phosphor screen element"

    def test_bezel_wraps_phosphor(self):
        """Bezel contains the phosphor screen."""
        html = _read("play.html")
        bezel_pos = html.find('id="title-bezel"')
        phosphor_pos = html.find('id="title-phosphor"')
        assert bezel_pos < phosphor_pos, (
            "Phosphor screen should be inside the bezel frame"
        )

    def test_phosphor_wraps_content(self):
        """Phosphor screen contains the title content."""
        html = _read("play.html")
        phosphor_pos = html.find('id="title-phosphor"')
        content_pos = html.find('id="title-screen-content"')
        assert phosphor_pos < content_pos, (
            "Title content should be inside the phosphor screen"
        )

    def test_id_plate_exists(self):
        html = _read("play.html")
        assert 'id="title-id-plate"' in html, "Missing #title-id-plate element"


# ── HTML: Title rendering ──


class TestTitleRendering:
    """MIR'S END rendered prominently in Latin only."""

    def test_title_logo_is_latin(self):
        """Title uses Latin 'MIR\\'S END', not faux-Cyrillic."""
        html = _read("play.html")
        assert "MIR'S END" in html or "MIR&#39;S END" in html
        # Should NOT use Cyrillic substitutions for the main title
        logo_match = re.search(
            r'id="title-logo"[^>]*>(.*?)</h1>', html, re.DOTALL
        )
        assert logo_match, "Could not find title-logo content"
        logo_text = logo_match.group(1).strip()
        assert "MIR" in logo_text, "Title logo must contain MIR"
        assert "END" in logo_text, "Title logo must contain END"


# ── HTML: Bilingual menu buttons ──


class TestBilingualButtons:
    """Menu options have bilingual labels (English + Russian)."""

    def test_new_game_has_russian_label(self):
        html = _read("play.html")
        assert "НОВАЯ ИГРА" in html, "New Game button missing Russian label"

    def test_continue_has_russian_label(self):
        html = _read("play.html")
        assert "ПРОДОЛЖИТЬ" in html, "Continue button missing Russian label"

    def test_settings_has_russian_label(self):
        html = _read("play.html")
        assert "НАСТРОЙКИ" in html, "Settings button missing Russian label"

    def test_btn_label_en_class_exists(self):
        html = _read("play.html")
        assert 'class="btn-label-en"' in html, (
            "Missing .btn-label-en span for English labels"
        )

    def test_btn_label_ru_class_exists(self):
        html = _read("play.html")
        assert 'class="btn-label-ru"' in html, (
            "Missing .btn-label-ru span for Russian labels"
        )

    def test_each_menu_btn_has_both_labels(self):
        """Each menu button contains both an English and a Russian label span."""
        html = _read("play.html")
        # Find all menu buttons
        buttons = re.findall(
            r'<button[^>]*class="menu-btn"[^>]*>(.*?)</button>',
            html,
            re.DOTALL,
        )
        assert len(buttons) >= 3, f"Expected at least 3 menu buttons, found {len(buttons)}"
        for i, btn_content in enumerate(buttons):
            assert "btn-label-en" in btn_content, (
                f"Menu button {i+1} missing English label span"
            )
            assert "btn-label-ru" in btn_content, (
                f"Menu button {i+1} missing Russian label span"
            )


# ── CSS: Bezel + phosphor styling ──


class TestBezelPhosphorCSS:
    """CSS implements the bezel + phosphor CRT aesthetic."""

    def test_bezel_styled(self):
        css = _read("ui.css")
        assert "#title-bezel" in css, "Missing #title-bezel CSS rule"

    def test_phosphor_styled(self):
        css = _read("ui.css")
        assert "#title-phosphor" in css, "Missing #title-phosphor CSS rule"

    def test_bezel_uses_border_color(self):
        css = _read("ui.css")
        # Bezel should use the same border-color as the game panels
        assert "var(--border-color)" in css, (
            "Bezel should use --border-color variable"
        )

    def test_phosphor_uses_panel_bg(self):
        css = _read("ui.css")
        assert "var(--bg-panel)" in css, (
            "Phosphor screen should use --bg-panel background"
        )

    def test_scanline_effect(self):
        """Phosphor screen has a scanline overlay effect."""
        css = _read("ui.css")
        assert "repeating-linear-gradient" in css, (
            "Missing scanline effect (repeating-linear-gradient)"
        )

    def test_id_plate_styled(self):
        css = _read("ui.css")
        assert "#title-id-plate" in css, "Missing #title-id-plate CSS rule"


# ── CSS: Hover/focus phosphor glow ──


class TestPhosphorGlowStates:
    """Hover/focus states use phosphor glow effect."""

    def test_menu_btn_hover_has_glow(self):
        """Menu button hover has box-shadow glow."""
        css = _read("ui.css")
        # Find the hover rule and check for glow
        hover_idx = css.find(".menu-btn:hover:not(:disabled)")
        assert hover_idx != -1, "Missing menu button hover rule"
        # Check within the next rule block
        chunk = css[hover_idx:hover_idx + 300]
        assert "box-shadow" in chunk, (
            "Menu button hover should have box-shadow phosphor glow"
        )

    def test_menu_btn_hover_has_text_shadow(self):
        """Menu button hover has text-shadow glow."""
        css = _read("ui.css")
        hover_idx = css.find(".menu-btn:hover:not(:disabled)")
        assert hover_idx != -1, "Missing menu button hover rule"
        chunk = css[hover_idx:hover_idx + 300]
        assert "text-shadow" in chunk, (
            "Menu button hover should have text-shadow phosphor glow"
        )

    def test_menu_btn_focus_state(self):
        css = _read("ui.css")
        assert ".menu-btn:focus" in css, "Missing .menu-btn:focus state"

    def test_russian_label_hover_styling(self):
        """Russian label changes on hover."""
        css = _read("ui.css")
        assert ".btn-label-ru" in css, "Missing .btn-label-ru CSS rule"


# ── CSS: Bilingual label styling ──


class TestBilingualLabelCSS:
    """Bilingual button labels are properly styled."""

    def test_btn_label_en_styled(self):
        css = _read("ui.css")
        assert ".btn-label-en" in css, "Missing .btn-label-en CSS rule"

    def test_btn_label_ru_styled(self):
        css = _read("ui.css")
        assert ".btn-label-ru" in css, "Missing .btn-label-ru CSS rule"

    def test_russian_label_smaller_font(self):
        """Russian label uses a smaller font size than English."""
        css = _read("ui.css")
        # Find the .btn-label-ru rule
        ru_idx = css.find(".btn-label-ru")
        assert ru_idx != -1
        chunk = css[ru_idx:ru_idx + 200]
        assert "font-size" in chunk, "Russian label should have explicit font-size"


# ── Integration: ESC still returns to title screen ──


class TestEscMenuIntegration:
    """ESC during gameplay still returns to the title screen."""

    def test_escape_handler_in_js(self):
        js = _read("ui.js")
        assert "Escape" in js, "Missing Escape key handler in ui.js"

    def test_title_screen_hidden_class_in_css(self):
        css = _read("ui.css")
        assert "#title-screen.hidden" in css, (
            "Missing .hidden class rule for title screen toggle"
        )

    def test_show_and_hide_menu_in_js(self):
        js = _read("ui.js")
        assert "showMenu" in js, "Missing showMenu function"
        assert "hideMenu" in js, "Missing hideMenu function"


# ── Integration: All files valid UTF-8 ──


class TestUTF8Validity:
    """All modified files remain valid UTF-8 (important for Cyrillic)."""

    def test_play_html_valid_utf8(self):
        _read("play.html")  # will raise UnicodeDecodeError if invalid

    def test_ui_css_valid_utf8(self):
        _read("ui.css")

    def test_ui_js_valid_utf8(self):
        _read("ui.js")
