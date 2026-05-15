"""M2 integration tests: Web UI — playable prototype verification.

Updated for #132: Soviet terminal visual language port.

Validates that the web UI shell forms a complete, playable interface:
- Story text is rendered in the 80×25 phosphor terminal grid
- Status data (O2, Morale, inventory) displayed in the sidebar column
- Text input accepts commands and supports history (up/down arrow)
- Terminal bezel layout with phosphor screen
- Dark theme with phosphor green palette
"""

import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


@pytest.fixture(scope="module")
def play_html():
    with open(os.path.join(GAME_DIR, "play.html")) as f:
        return f.read()


@pytest.fixture(scope="module")
def ui_css():
    with open(os.path.join(GAME_DIR, "ui.css")) as f:
        return f.read()


@pytest.fixture(scope="module")
def ui_js():
    with open(os.path.join(GAME_DIR, "ui.js")) as f:
        return f.read()


# ── Text Panel ────────────────────────────────────────────────────────


class TestTextPanel:
    """Story text is rendered in the 80×25 pre-based terminal grid."""

    def test_story_output_container_exists(self, play_html):
        assert 'id="story-output"' in play_html

    def test_display_pre_exists(self, play_html):
        """The <pre id="display"> element renders the terminal grid."""
        assert 'id="display"' in play_html

    def test_story_text_class_styled(self, ui_css):
        assert ".story-text" in ui_css

    def test_player_input_class_styled(self, ui_css):
        """Player input is visually distinct (bold, different color)."""
        assert ".player-input" in ui_css

    def test_system_text_class_styled(self, ui_css):
        """System messages styled differently (dim, italic)."""
        assert ".system-text" in ui_css

    def test_append_story_text_function(self, ui_js):
        """JS has function to append story output."""
        assert "function appendStoryText" in ui_js

    def test_append_player_input_function(self, ui_js):
        """JS has function to echo player commands."""
        assert "function appendPlayerInput" in ui_js
        # Should prefix with ">"
        assert "> " in ui_js

    def test_render_display_function(self, ui_js):
        """JS has renderDisplay for updating the <pre> grid."""
        assert "renderDisplay" in ui_js


# ── Scene Art ────────────────────────────────────────────────────────


class TestSceneArtPanel:
    """Scene art is loaded and cached on room changes."""

    def test_room_art_mapping_covers_all_rooms(self, ui_js):
        """ROOM_ART maps every game room to an ASCII art file."""
        for room in ["crew quarters", "main corridor", "command module",
                      "observation cupola"]:
            assert room in ui_js.lower(), f"Missing room-art mapping: {room}"

    def test_darkness_has_art(self, ui_js):
        """Initial darkness state has its own art."""
        assert '"darkness"' in ui_js
        assert "darkness.txt" in ui_js

    def test_scene_art_fetched_via_network(self, ui_js):
        """Scene art is loaded via fetch (not inline)."""
        assert "fetch(" in ui_js

    def test_art_cache_prevents_refetch(self, ui_js):
        """Fetched art is cached to avoid redundant requests."""
        assert "artCache" in ui_js

    def test_room_change_triggers_art_load(self, ui_js):
        """setCurrentRoom triggers loadSceneArt."""
        assert "loadSceneArt" in ui_js
        set_room_fn = ui_js[ui_js.find("function setCurrentRoom"):]
        set_room_fn = set_room_fn[:set_room_fn.find("\n  }") + 4]
        assert "loadSceneArt" in set_room_fn

    def test_detect_room_change_from_story_text(self, ui_js):
        """detectRoomChange parses room names from interpreter output."""
        assert "function detectRoomChange" in ui_js
        assert "KNOWN_ROOMS" in ui_js


# ── Status Display ──────────────────────────────────────────────────


class TestStatusPanel:
    """Status data (O2, morale, inventory) is rendered in the sidebar column."""

    def test_sidebar_shows_o2(self, ui_js):
        """O2 is displayed in the sidebar via compose()."""
        assert "O2 LEVEL" in ui_js or "o2" in ui_js.lower()

    def test_sidebar_shows_morale(self, ui_js):
        """Morale is displayed in the sidebar via compose()."""
        assert "MORALE" in ui_js

    def test_sidebar_shows_inventory(self, ui_js):
        """Inventory is displayed in the sidebar."""
        assert "ИНВЕНТАРЬ" in ui_js

    def test_update_status_function(self, ui_js):
        """JS updates status display dynamically."""
        assert "function updateStatus" in ui_js

    def test_inventory_empty_state(self, ui_js):
        """Empty inventory displays a placeholder message."""
        assert "Nothing carried" in ui_js

    def test_inventory_renders_items(self, ui_js):
        """Inventory items are rendered in the sidebar."""
        assert "state.inventory" in ui_js

    def test_compose_builds_sidebar(self, ui_js):
        """compose() includes sidebar with vitals and systems."""
        assert "buildSidebar" in ui_js
        assert "СОСТОЯНИЕ" in ui_js
        assert "СИСТЕМЫ" in ui_js


# ── Text Input ────────────────────────────────────────────────────────


class TestTextInput:
    """Text input accepts commands and supports history."""

    def test_command_input_exists(self, play_html):
        assert 'id="command-input"' in play_html
        assert 'type="text"' in play_html

    def test_enter_key_sends_command(self, ui_js):
        assert '"Enter"' in ui_js
        assert "sendToInterpreter" in ui_js

    def test_arrow_up_cycles_history(self, ui_js):
        assert '"ArrowUp"' in ui_js
        assert "historyIndex" in ui_js

    def test_arrow_down_cycles_history(self, ui_js):
        assert '"ArrowDown"' in ui_js

    def test_history_stored_in_array(self, ui_js):
        assert "commandHistory" in ui_js
        assert "state.commandHistory.push" in ui_js

    def test_empty_input_ignored(self, ui_js):
        """Empty commands are not sent."""
        assert "cmd.length === 0" in ui_js or "trim()" in ui_js

    def test_input_cleared_after_submit(self, ui_js):
        """Input field is cleared after submitting a command."""
        assert 'commandInput.value = ""' in ui_js


# ── Terminal Layout ──────────────────────────────────────────────────


class TestTerminalLayout:
    """Layout uses Soviet terminal bezel with phosphor screen."""

    def test_terminal_bezel_exists(self, play_html):
        assert 'id="terminal"' in play_html

    def test_screen_element(self, play_html):
        assert 'id="screen"' in play_html

    def test_grid_layout(self, ui_css):
        """Terminal uses CSS grid."""
        assert "display: grid" in ui_css

    def test_80x25_grid_constants(self, ui_js):
        """JS defines 80×25 grid constants."""
        assert "TOTAL_W" in ui_js
        assert "STORY_W" in ui_js
        assert "SIDE_W" in ui_js
        assert "= 80" in ui_js
        assert "= 48" in ui_js
        assert "= 25" in ui_js

    def test_box_drawing_characters(self, ui_js):
        """compose() uses box-drawing characters for borders."""
        # Check for Unicode escape references to box-drawing chars
        assert "\\u2554" in ui_js or "\u2554" in ui_js, "Missing top-left corner"
        assert "\\u2550" in ui_js or "\u2550" in ui_js, "Missing horizontal border"
        assert "\\u2551" in ui_js or "\u2551" in ui_js, "Missing vertical border"

    def test_bezel_plate(self, play_html):
        """Bezel includes the etched ID plate."""
        assert 'id="bezel-plate"' in play_html
        assert "MIR-2" in play_html

    def test_scanline_effect(self, play_html):
        """Screen has a scanline overlay element."""
        assert 'id="scan-line"' in play_html

    def test_screws(self, play_html):
        """Bezel has corner screws."""
        assert 'class="screw' in play_html


# ── Dark Theme ────────────────────────────────────────────────────────


class TestDarkTheme:
    """Dark theme renders correctly with phosphor green palette."""

    def test_dark_background_variable(self, ui_css):
        assert "--bg-dark: #0a0c10" in ui_css

    def test_panel_background(self, ui_css):
        assert "--bg-panel: #0d1117" in ui_css

    def test_input_background(self, ui_css):
        assert "--bg-input" in ui_css

    def test_text_colors_defined(self, ui_css):
        assert "--text-primary" in ui_css
        assert "--text-dim" in ui_css
        assert "--text-input" in ui_css

    def test_border_colors_defined(self, ui_css):
        assert "--border-color" in ui_css
        assert "--border-glow" in ui_css

    def test_phosphor_colors(self, ui_css):
        """Phosphor green palette is defined."""
        assert "--phosphor:" in ui_css
        assert "--phosphor-dim:" in ui_css
        assert "--phosphor-bright:" in ui_css

    def test_scene_blue_colors(self, ui_css):
        """Legacy scene blue variables still present for modal compat."""
        assert "--scene-blue" in ui_css
        assert "--scene-text" in ui_css

    def test_status_colors_defined(self, ui_css):
        """Status colors: green for good, yellow warning, red danger."""
        assert "--status-green" in ui_css
        assert "--status-yellow" in ui_css
        assert "--status-red" in ui_css

    def test_monospace_font(self, ui_css):
        """Theme uses IBM Plex Mono as primary font."""
        assert "monospace" in ui_css
        assert "IBM Plex Mono" in ui_css

    def test_custom_scrollbar(self, ui_css):
        """Scrollbar is styled to match dark theme."""
        assert "scrollbar" in ui_css

    def test_title_styling(self, ui_css):
        """Game title has distinctive styling."""
        assert "--title-color" in ui_css
        assert "letter-spacing" in ui_css
        assert "text-transform: uppercase" in ui_css

    def test_no_white_backgrounds(self, ui_css):
        """No white or light backgrounds that would break the dark theme."""
        assert "background: white" not in ui_css
        assert "background: #fff" not in ui_css
        assert "background: #ffffff" not in ui_css


# ── Interpreter Integration ───────────────────────────────────────────


class TestInterpreterIntegration:
    """UI hooks into Glulx interpreters for full game play."""

    def test_glulx_story_reference(self, play_html):
        """HTML references the compiled story file."""
        assert "dist/story.ulx" in play_html

    def test_parchment_config(self, play_html):
        """Parchment interpreter configuration present."""
        assert "parchment_options" in play_html

    def test_gameport_div(self, play_html):
        """Hidden gameport div for interpreter attachment."""
        assert 'id="gameport"' in play_html

    def test_hook_interpreter_function(self, ui_js):
        """JS hooks into available interpreters."""
        assert "function hookInterpreter" in ui_js

    def test_glkote_support(self, ui_js):
        """GlkOte (Quixe) interpreter support."""
        assert "GlkOte" in ui_js
        assert "function hookGlkOte" in ui_js

    def test_parchment_support(self, ui_js):
        """Parchment interpreter support."""
        assert "function hookParchment" in ui_js

    def test_shell_fallback(self, ui_js):
        """Standalone shell mode when no interpreter is loaded."""
        assert "function handleShellCommand" in ui_js

    def test_public_api_exposed(self, ui_js):
        """Public API exposed for external integration."""
        assert "window.MirsEnd" in ui_js

    def test_public_api_has_required_methods(self, ui_js):
        """MirsEnd API includes appendStoryText, setState, getState."""
        for method in ["appendStoryText", "appendPlayerInput",
                       "appendSystemText", "setCurrentRoom",
                       "updateStatus", "getState", "setState"]:
            assert method in ui_js, f"Missing public API method: {method}"

    def test_noscript_fallback(self, play_html):
        """Noscript tag provides fallback for JS-disabled browsers."""
        assert "<noscript>" in play_html
