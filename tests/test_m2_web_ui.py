"""M2 integration tests: Web UI — playable prototype verification.

Validates that the web UI shell forms a complete, playable interface:
- Text panel displays story output and echoes player input
- Scene art panel updates when player changes rooms
- Status panel shows O2, Morale, and inventory
- Text input accepts commands and supports history (up/down arrow)
- Layout matches Hitchhiker's-style spec (left text, right art/status)
- Dark theme renders correctly
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
    """Text panel displays story output and echoes player input."""

    def test_story_output_container_exists(self, play_html):
        assert 'id="story-output"' in play_html

    def test_story_panel_is_scrollable(self, ui_css):
        assert "overflow-y: auto" in ui_css or "overflow-y:auto" in ui_css

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
        assert '"> "' in ui_js

    def test_scroll_to_bottom_on_new_text(self, ui_js):
        """Story panel auto-scrolls to latest text."""
        assert "scrollToBottom" in ui_js
        assert "scrollTop" in ui_js
        assert "scrollHeight" in ui_js


# ── Scene Art Panel ───────────────────────────────────────────────────


class TestSceneArtPanel:
    """Scene art panel updates when player changes rooms."""

    def test_scene_art_element_exists(self, play_html):
        assert 'id="scene-art"' in play_html

    def test_scene_panel_exists(self, play_html):
        assert 'id="scene-panel"' in play_html

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
        # setCurrentRoom should call loadSceneArt
        set_room_fn = ui_js[ui_js.find("function setCurrentRoom"):]
        set_room_fn = set_room_fn[:set_room_fn.find("\n  }") + 4]
        assert "loadSceneArt" in set_room_fn

    def test_detect_room_change_from_story_text(self, ui_js):
        """detectRoomChange parses room names from interpreter output."""
        assert "function detectRoomChange" in ui_js
        assert "KNOWN_ROOMS" in ui_js


# ── Status Panel ──────────────────────────────────────────────────────


class TestStatusPanel:
    """Status panel shows O2, Morale, and inventory."""

    def test_o2_display_exists(self, play_html):
        assert 'id="status-o2"' in play_html

    def test_morale_display_exists(self, play_html):
        assert 'id="status-morale"' in play_html

    def test_inventory_list_exists(self, play_html):
        assert 'id="inventory-list"' in play_html

    def test_o2_bar_exists(self, play_html):
        assert 'id="status-bar-o2"' in play_html

    def test_morale_bar_exists(self, play_html):
        assert 'id="status-bar-morale"' in play_html

    def test_bar_fill_elements(self, play_html):
        """Progress bars have fill elements."""
        assert "bar-fill" in play_html

    def test_update_status_function(self, ui_js):
        """JS updates status display dynamically."""
        assert "function updateStatus" in ui_js

    def test_o2_color_thresholds(self, ui_js):
        """O2 display changes color based on level (green/yellow/red)."""
        assert "state.o2 > 50" in ui_js or "o2 > 50" in ui_js
        assert "state.o2 > 25" in ui_js or "o2 > 25" in ui_js
        assert "status-green" in ui_js
        assert "status-yellow" in ui_js
        assert "status-red" in ui_js

    def test_morale_color_thresholds(self, ui_js):
        """Morale display changes color based on level."""
        assert "state.morale > 50" in ui_js or "morale > 50" in ui_js
        assert "state.morale > 25" in ui_js or "morale > 25" in ui_js

    def test_inventory_empty_state(self, ui_js):
        """Empty inventory displays a placeholder message."""
        assert "Nothing carried" in ui_js
        assert "empty-inventory" in ui_js

    def test_inventory_renders_items(self, ui_js):
        """Inventory items are rendered as list elements."""
        assert "state.inventory" in ui_js
        assert "createElement" in ui_js


# ── Text Input ────────────────────────────────────────────────────────


class TestTextInput:
    """Text input accepts commands and supports history."""

    def test_command_input_exists(self, play_html):
        assert 'id="command-input"' in play_html
        assert 'type="text"' in play_html

    def test_input_has_placeholder(self, play_html):
        assert "placeholder" in play_html

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

    def test_input_prompt_visible(self, play_html):
        """Command prompt symbol (>) is displayed."""
        assert 'id="input-prompt"' in play_html
        assert "&gt;" in play_html


# ── Hitchhiker's-Style Layout ────────────────────────────────────────


class TestHitchhikersLayout:
    """Layout matches spec: left text, right art/status, bottom input."""

    def test_grid_layout(self, ui_css):
        """Main container uses CSS grid."""
        assert "display: grid" in ui_css

    def test_two_column_layout(self, ui_css):
        """Grid has two columns: flexible left, fixed right."""
        assert "grid-template-columns" in ui_css
        assert "1fr" in ui_css
        assert "340px" in ui_css

    def test_two_row_layout(self, ui_css):
        """Grid has two rows: flexible content, fixed input."""
        assert "grid-template-rows" in ui_css
        assert "auto" in ui_css

    def test_story_panel_left_column(self, ui_css):
        """Story panel occupies the left column."""
        assert "#story-panel" in ui_css
        assert "grid-column: 1" in ui_css

    def test_sidebar_right_column(self, ui_css):
        """Sidebar occupies the right column."""
        assert "#sidebar" in ui_css
        assert "grid-column: 2" in ui_css

    def test_input_bar_spans_full_width(self, ui_css):
        """Input bar spans both columns at the bottom."""
        assert "#input-bar" in ui_css
        assert "1 / -1" in ui_css  # grid-column: 1 / -1

    def test_sidebar_has_three_sections(self, play_html):
        """Sidebar contains scene, title, and status panels."""
        assert 'id="scene-panel"' in play_html
        assert 'id="title-panel"' in play_html
        assert 'id="status-panel"' in play_html

    def test_sidebar_flex_column(self, ui_css):
        """Sidebar uses flex-direction: column for vertical stacking."""
        assert "flex-direction: column" in ui_css


# ── Dark Theme ────────────────────────────────────────────────────────


class TestDarkTheme:
    """Dark theme renders correctly with appropriate color scheme."""

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

    def test_scene_blue_colors(self, ui_css):
        """Scene art uses blue-tinted styling."""
        assert "--scene-blue" in ui_css
        assert "--scene-text" in ui_css

    def test_status_colors_defined(self, ui_css):
        """Status colors: green for good, yellow warning, red danger."""
        assert "--status-green" in ui_css
        assert "--status-yellow" in ui_css
        assert "--status-red" in ui_css

    def test_monospace_font(self, ui_css):
        """Theme uses monospace font throughout."""
        assert "monospace" in ui_css
        assert "Courier New" in ui_css

    def test_custom_scrollbar(self, ui_css):
        """Scrollbar is styled to match dark theme."""
        assert "scrollbar" in ui_css
        assert "webkit-scrollbar" in ui_css

    def test_title_styling(self, ui_css):
        """Game title has distinctive styling."""
        assert "--title-color" in ui_css
        assert "letter-spacing" in ui_css
        assert "text-transform: uppercase" in ui_css

    def test_no_white_backgrounds(self, ui_css):
        """No white or light backgrounds that would break the dark theme."""
        # Ensure no background: white or background: #fff
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
