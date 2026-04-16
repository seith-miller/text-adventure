"""Tests for the title screen and menu system (issue #14)."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── Helper ──


def _read(filename):
    path = os.path.join(GAME_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── HTML: Title screen structure ──


class TestTitleScreenHTML:
    """Title screen overlay is present in play.html."""

    def test_title_screen_element_exists(self):
        html = _read("play.html")
        assert 'id="title-screen"' in html, "Missing #title-screen overlay"

    def test_title_logo_displays_game_name(self):
        html = _read("play.html")
        assert 'id="title-logo"' in html, "Missing #title-logo element"
        assert "MIR'S END" in html or "MIR&#39;S END" in html, (
            "Title logo does not display game name"
        )

    def test_title_subtitle_exists(self):
        html = _read("play.html")
        assert 'id="title-subtitle"' in html, "Missing subtitle element"

    def test_new_game_button_exists(self):
        html = _read("play.html")
        assert 'id="menu-new-game"' in html, "Missing New Game button"
        assert "New Game" in html, "New Game button text missing"

    def test_continue_button_exists(self):
        html = _read("play.html")
        assert 'id="menu-continue"' in html, "Missing Continue button"
        assert "Continue" in html, "Continue button text missing"

    def test_continue_button_disabled_by_default(self):
        html = _read("play.html")
        # The continue button should have the disabled attribute in HTML
        # Find the continue button element and check for disabled
        match = re.search(r'<button[^>]*id="menu-continue"[^>]*>', html)
        assert match, "Continue button not found"
        assert "disabled" in match.group(0), (
            "Continue button should be disabled by default"
        )

    def test_settings_button_exists(self):
        html = _read("play.html")
        assert 'id="menu-settings"' in html, "Missing Settings button"
        assert "Settings" in html, "Settings button text missing"

    def test_settings_button_disabled_placeholder(self):
        html = _read("play.html")
        match = re.search(r'<button[^>]*id="menu-settings"[^>]*>', html)
        assert match, "Settings button not found"
        assert "disabled" in match.group(0), (
            "Settings button should be disabled (placeholder)"
        )

    def test_menu_buttons_have_menu_btn_class(self):
        html = _read("play.html")
        buttons = re.findall(r'<button[^>]*class="menu-btn"[^>]*>', html)
        assert len(buttons) >= 3, (
            f"Expected at least 3 menu buttons with class menu-btn, found {len(buttons)}"
        )

    def test_title_menu_nav_exists(self):
        html = _read("play.html")
        assert 'id="title-menu"' in html, "Missing #title-menu nav container"

    def test_ingame_menu_button_exists(self):
        html = _read("play.html")
        assert 'id="ingame-menu-btn"' in html, "Missing in-game menu button"

    def test_title_screen_before_game_shell(self):
        """Title screen overlay appears before the game shell in DOM order."""
        html = _read("play.html")
        title_pos = html.find('id="title-screen"')
        shell_pos = html.find('id="game-shell"')
        assert title_pos < shell_pos, (
            "Title screen should appear before game shell in DOM"
        )


# ── CSS: Title screen styling ──


class TestTitleScreenCSS:
    """Title screen has appropriate styling in ui.css."""

    def test_title_screen_overlay_styled(self):
        css = _read("ui.css")
        assert "#title-screen" in css, "Missing #title-screen CSS rule"

    def test_title_screen_uses_fixed_position(self):
        css = _read("ui.css")
        # Title screen should overlay the game using fixed positioning
        assert "position: fixed" in css or "position:fixed" in css, (
            "Title screen should use fixed positioning"
        )

    def test_title_screen_has_z_index(self):
        css = _read("ui.css")
        # Should have high z-index to overlay everything
        assert "z-index" in css, "Title screen needs z-index for layering"

    def test_title_screen_hidden_class(self):
        css = _read("ui.css")
        assert "#title-screen.hidden" in css, (
            "Missing .hidden class rule for title screen"
        )

    def test_title_logo_styled(self):
        css = _read("ui.css")
        assert "#title-logo" in css, "Missing #title-logo CSS rule"

    def test_menu_button_styled(self):
        css = _read("ui.css")
        assert ".menu-btn" in css, "Missing .menu-btn CSS rule"

    def test_menu_button_hover_state(self):
        css = _read("ui.css")
        assert ".menu-btn:hover" in css, "Missing .menu-btn hover state"

    def test_menu_button_disabled_state(self):
        css = _read("ui.css")
        assert ".menu-btn:disabled" in css, "Missing .menu-btn disabled state"

    def test_ingame_menu_button_styled(self):
        css = _read("ui.css")
        assert "#ingame-menu-btn" in css, "Missing #ingame-menu-btn CSS rule"

    def test_title_screen_uses_theme_colors(self):
        """Title screen uses existing theme CSS variables."""
        css = _read("ui.css")
        # Find the title-screen section and verify it uses theme vars
        assert "var(--bg-dark)" in css, "Title screen should use --bg-dark"
        assert "var(--title-color)" in css, "Title should use --title-color"


# ── JavaScript: Menu logic ──


class TestMenuJavaScript:
    """Menu system logic in ui.js."""

    def test_game_started_state_flag(self):
        js = _read("ui.js")
        assert "gameStarted" in js, "Missing gameStarted state flag"

    def test_show_menu_function(self):
        js = _read("ui.js")
        assert "showMenu" in js, "Missing showMenu function"

    def test_hide_menu_function(self):
        js = _read("ui.js")
        assert "hideMenu" in js, "Missing hideMenu function"

    def test_start_new_game_function(self):
        js = _read("ui.js")
        assert "startNewGame" in js, "Missing startNewGame function"

    def test_continue_game_function(self):
        js = _read("ui.js")
        assert "continueGame" in js, "Missing continueGame function"

    def test_save_game_function(self):
        js = _read("ui.js")
        assert "saveGame" in js, "Missing saveGame function"

    def test_escape_key_handler(self):
        js = _read("ui.js")
        assert "Escape" in js, "Missing Escape key handler"

    def test_localstorage_save_key(self):
        js = _read("ui.js")
        assert "SAVE_KEY" in js or "mirsend_save" in js, (
            "Missing localStorage save key"
        )

    def test_check_saved_game_function(self):
        js = _read("ui.js")
        assert "checkSavedGame" in js or "localStorage" in js, (
            "Missing saved game check"
        )

    def test_new_game_resets_state(self):
        """startNewGame should reset o2, morale, inventory."""
        js = _read("ui.js")
        # Find startNewGame function and verify it resets key state
        start_idx = js.find("function startNewGame")
        assert start_idx != -1, "startNewGame function not found"
        # Check within ~500 chars of the function
        chunk = js[start_idx:start_idx + 600]
        assert "o2" in chunk, "startNewGame should reset o2"
        assert "morale" in chunk, "startNewGame should reset morale"
        assert "inventory" in chunk, "startNewGame should reset inventory"

    def test_menu_exposed_in_public_api(self):
        js = _read("ui.js")
        assert "showMenu" in js, "showMenu missing from public API"
        assert "saveGame" in js, "saveGame missing from public API"

    def test_menu_new_game_event_listener(self):
        js = _read("ui.js")
        assert "menu-new-game" in js, "Missing event listener for New Game button"

    def test_menu_continue_event_listener(self):
        js = _read("ui.js")
        assert "menu-continue" in js, "Missing event listener for Continue button"

    def test_ingame_menu_btn_event_listener(self):
        js = _read("ui.js")
        assert "ingame-menu-btn" in js, (
            "Missing event listener for in-game menu button"
        )

    def test_init_shows_menu_on_launch(self):
        """init() should show the title screen, not start gameplay immediately."""
        js = _read("ui.js")
        init_idx = js.find("function init()")
        assert init_idx != -1, "init function not found"
        chunk = js[init_idx:init_idx + 1200]
        assert "showMenu" in chunk, (
            "init should call showMenu to display title screen on launch"
        )

    def test_continue_restores_state(self):
        """continueGame should restore state from localStorage."""
        js = _read("ui.js")
        continue_idx = js.find("function continueGame")
        assert continue_idx != -1, "continueGame function not found"
        chunk = js[continue_idx:continue_idx + 600]
        assert "localStorage" in chunk or "SAVE_KEY" in chunk, (
            "continueGame should read from localStorage"
        )
        assert "JSON.parse" in chunk, (
            "continueGame should parse saved JSON data"
        )


# ── Integration: All pieces connected ──


class TestMenuIntegration:
    """Title screen, CSS, and JS work together."""

    def test_html_js_button_ids_match(self):
        """Button IDs in HTML match the IDs referenced in JavaScript."""
        html = _read("play.html")
        js = _read("ui.js")
        ids = ["menu-new-game", "menu-continue", "menu-settings", "ingame-menu-btn"]
        for btn_id in ids:
            assert btn_id in html, f"Button #{btn_id} missing from HTML"
            # menu-settings may not have a JS handler yet (placeholder)
            if btn_id != "menu-settings":
                assert btn_id in js, f"Button #{btn_id} not referenced in JS"

    def test_css_classes_used_in_html(self):
        """CSS classes defined in ui.css are used in play.html."""
        html = _read("play.html")
        assert "menu-btn" in html, "menu-btn class not used in HTML"

    def test_hidden_class_used_in_js(self):
        """JavaScript uses the .hidden CSS class to toggle title screen."""
        js = _read("ui.js")
        assert "hidden" in js, "JS should toggle 'hidden' class on title screen"

    def test_all_ui_files_valid_utf8(self):
        """All modified UI files are valid UTF-8."""
        for filename in ["play.html", "ui.css", "ui.js"]:
            path = os.path.join(GAME_DIR, filename)
            with open(path, encoding="utf-8") as f:
                try:
                    f.read()
                except UnicodeDecodeError:
                    raise AssertionError(f"{filename} is not valid UTF-8")
