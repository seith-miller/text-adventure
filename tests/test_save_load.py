"""Tests for the save/load game system (issue #15)."""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── save-manager.js existence and structure ──


def test_save_manager_js_exists():
    """save-manager.js exists in the game directory."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    assert os.path.isfile(path), "game/save-manager.js not found"


def test_save_manager_is_valid_utf8():
    """save-manager.js is valid UTF-8."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path, encoding="utf-8") as f:
        f.read()


def test_save_manager_has_storage_prefix():
    """SaveManager uses a namespaced storage prefix to avoid collisions."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "STORAGE_PREFIX" in content, "Missing storage prefix constant"
    assert "mirsend_" in content, "Storage prefix should include game name"


def test_save_manager_has_multiple_slots():
    """SaveManager supports at least 3 save slots."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "SLOT_COUNT" in content, "Missing SLOT_COUNT constant"
    # Extract SLOT_COUNT value
    match = re.search(r"SLOT_COUNT\s*=\s*(\d+)", content)
    assert match, "Could not parse SLOT_COUNT value"
    assert int(match.group(1)) >= 3, "Need at least 3 save slots"


def test_save_manager_has_auto_save():
    """SaveManager has auto-save functionality."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "AUTO_SAVE_KEY" in content, "Missing auto-save key"
    assert "autoSave" in content, "Missing autoSave function"
    assert "loadAutoSave" in content, "Missing loadAutoSave function"


def test_save_manager_has_slot_operations():
    """SaveManager provides save, load, and delete per slot."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "saveToSlot" in content, "Missing saveToSlot function"
    assert "loadFromSlot" in content, "Missing loadFromSlot function"
    assert "deleteSlot" in content, "Missing deleteSlot function"


def test_save_manager_checks_storage_availability():
    """SaveManager checks if localStorage is available."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "storageAvailable" in content, "Missing storageAvailable check"
    assert "localStorage" in content, "Missing localStorage usage"


def test_save_manager_captures_state():
    """SaveManager captures game state for serialization."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "captureState" in content, "Missing captureState function"
    assert "timestamp" in content, "Save data should include a timestamp"
    assert "currentRoom" in content, "Save data should include current room"
    assert "o2" in content, "Save data should include O2 level"
    assert "morale" in content, "Save data should include morale level"
    assert "inventory" in content, "Save data should include inventory"


def test_save_manager_applies_state():
    """SaveManager can apply loaded state back to the game."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "applyState" in content, "Missing applyState function"
    assert "MirsEnd" in content, "applyState should interact with MirsEnd API"


def test_save_manager_lists_slots():
    """SaveManager can list all save slots with summaries."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "listSlots" in content, "Missing listSlots function"
    assert "slotSummary" in content, "Missing slotSummary function"


def test_save_manager_gets_most_recent():
    """SaveManager can find the most recent save across all slots."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "getMostRecentSave" in content, "Missing getMostRecentSave function"


def test_save_manager_exposes_public_api():
    """SaveManager exposes its API on window.SaveManager."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "window.SaveManager" in content, "Missing window.SaveManager public API"


def test_save_manager_returns_result_objects():
    """Save/load operations return {success, message} result objects."""
    path = os.path.join(GAME_DIR, "save-manager.js")
    with open(path) as f:
        content = f.read()
    assert "success:" in content or '"success"' in content, (
        "Missing success field in results"
    )
    assert "message:" in content or '"message"' in content, (
        "Missing message field in results"
    )


# ── ui.js save/load integration ──


def test_ui_js_has_save_command():
    """ui.js handles the SAVE command in shell mode."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    # Check that "save" is handled as a command
    assert '"save"' in content, "Missing save command handling"
    assert "quickSave" in content, "Missing quickSave function"


def test_ui_js_has_restore_command():
    """ui.js handles the RESTORE command in shell mode."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert '"restore"' in content, "Missing restore command handling"
    assert "quickLoad" in content, "Missing quickLoad function"


def test_ui_js_has_auto_save_on_room_change():
    """ui.js triggers auto-save when entering a new area."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "autoSave" in content, "Missing auto-save call"
    # Auto-save should be in setCurrentRoom
    room_fn_match = re.search(
        r"function setCurrentRoom.*?\n(?:.*\n)*?.*autoSave", content
    )
    assert room_fn_match, "Auto-save should trigger in setCurrentRoom"


def test_ui_js_has_save_load_modal():
    """ui.js has a save/load modal UI."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "showSaveLoadModal" in content, "Missing showSaveLoadModal function"
    assert "closeSaveLoadModal" in content, "Missing closeSaveLoadModal function"
    assert "save-load-overlay" in content, "Missing modal overlay element"
    assert "save-load-modal" in content, "Missing modal element"


def test_ui_js_has_continue_game():
    """ui.js has a continue-from-last-save function."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "continueGame" in content, "Missing continueGame function"
    assert "getMostRecentSave" in content, (
        "continueGame should use getMostRecentSave"
    )


def test_ui_js_save_load_in_help():
    """Shell help text mentions save and restore commands."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "save" in content.lower() and "restore" in content.lower(), (
        "Help text should mention save/restore commands"
    )


def test_ui_js_has_save_load_buttons_init():
    """ui.js initializes save/load button event listeners."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "initSaveLoadButtons" in content, (
        "Missing initSaveLoadButtons function"
    )
    assert "btn-save" in content, "Missing btn-save element reference"
    assert "btn-load" in content, "Missing btn-load element reference"
    assert "btn-continue" in content, "Missing btn-continue element reference"


def test_ui_js_exposes_save_load_api():
    """MirsEnd public API includes save/load functions."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "showSaveModal" in content, "Missing showSaveModal in public API"
    assert "showLoadModal" in content, "Missing showLoadModal in public API"
    assert "quickSave" in content, "Missing quickSave in public API"
    assert "quickLoad" in content, "Missing quickLoad in public API"
    assert "continueGame" in content, "Missing continueGame in public API"


def test_ui_js_save_load_feedback():
    """Save/load operations provide user feedback via system messages."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path) as f:
        content = f.read()
    assert "appendSystemText" in content, "Missing system text for feedback"
    # Check that save/load results are displayed
    assert "Auto-saved" in content, "Missing auto-save feedback message"
    assert "result.message" in content, "Save/load result messages not displayed"


# ── play.html save/load UI ──


def test_play_html_has_save_load_buttons():
    """play.html includes save, load, and continue buttons."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="btn-save"' in content, "Missing save button"
    assert 'id="btn-load"' in content, "Missing load button"
    assert 'id="btn-continue"' in content, "Missing continue button"


def test_play_html_loads_save_manager():
    """play.html loads save-manager.js via <script> before the ui.js tag."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'src="save-manager.js"' in content, (
        "play.html does not reference save-manager.js"
    )
    sm_pos = content.index('src="save-manager.js"')
    ui_pos = content.index('src="ui.js"')
    assert sm_pos < ui_pos, "save-manager.js must load before ui.js"


def test_play_html_save_load_buttons_container():
    """Save/load buttons are in a dedicated container (may be hidden)."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'id="save-load-buttons"' in content, (
        "Missing save-load-buttons container"
    )


# ── ui.css save/load styles ──


def test_ui_css_has_save_load_button_styles():
    """CSS styles the save/load buttons."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert ".sl-btn" in content, "Missing .sl-btn button styles"
    assert "#save-load-buttons" in content, "Missing save-load-buttons styles"


def test_ui_css_has_modal_styles():
    """CSS styles the save/load modal overlay."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "#save-load-overlay" in content, "Missing modal overlay styles"
    assert "#save-load-modal" in content, "Missing modal styles"


def test_ui_css_has_save_slot_styles():
    """CSS styles the save slot rows in the modal."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert ".save-slot-row" in content, "Missing save slot row styles"
    assert ".save-slot-btn" in content, "Missing save slot button styles"
    assert ".save-slot-label" in content, "Missing save slot label styles"
    assert ".save-slot-summary" in content, "Missing save slot summary styles"


def test_ui_css_modal_has_z_index():
    """Modal overlay has a z-index to appear above game UI."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path) as f:
        content = f.read()
    assert "z-index" in content, "Modal overlay should have z-index"
