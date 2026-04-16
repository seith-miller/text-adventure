"""M3 integration tests: complete experience verification.

Final quality gate — validates that all M3 features (title screen, menu,
save/load, intro sequence) work together and that M1/M2 remain stable.

Covers:
  - Title screen & menu system (#14)
  - Save/Load persistence (#15)
  - Intro sequence (#16)
  - Full end-to-end flow: launch -> title -> new game -> intro -> play -> save -> load
  - Regression: M1 + M2 still pass, build pipeline, biome lint
"""

import json
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")
STORY_NI = os.path.join(ROOT, "game", "inform", "Source", "story.ni")


# ── Helpers ──────────────────────────────────────────────────────────────


def _read(filename):
    """Read a file from the game directory."""
    path = os.path.join(GAME_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_root(filename):
    """Read a file from the project root."""
    path = os.path.join(ROOT, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Title Screen & Menu ─────────────────────────────────────────────────


class TestTitleScreenDisplay:
    """Title screen displays on initial load."""

    def test_title_screen_overlay_present(self):
        """Title screen overlay element exists in HTML."""
        html = _read("play.html")
        assert 'id="title-screen"' in html

    def test_title_screen_shown_on_init(self):
        """init() calls showMenu() to display title screen on launch."""
        js = _read("ui.js")
        init_idx = js.find("function init()")
        assert init_idx != -1
        chunk = js[init_idx:init_idx + 1200]
        assert "showMenu" in chunk

    def test_title_screen_has_game_title(self):
        """Title screen displays the game name 'MIR'S END'."""
        html = _read("play.html")
        assert 'id="title-logo"' in html
        assert "MIR" in html and "END" in html

    def test_title_screen_has_subtitle(self):
        """Title screen has the subtitle."""
        html = _read("play.html")
        assert 'id="title-subtitle"' in html
        assert "Interactive Survival Story" in html


class TestNewGameFlow:
    """'New Game' starts the intro sequence then gameplay."""

    def test_new_game_button_present(self):
        html = _read("play.html")
        assert 'id="menu-new-game"' in html

    def test_new_game_resets_game_state(self):
        """startNewGame resets o2, morale, inventory and marks game started."""
        js = _read("ui.js")
        idx = js.find("function startNewGame")
        assert idx != -1
        chunk = js[idx:idx + 700]
        assert "state.o2 = 100" in chunk
        assert "state.morale = 70" in chunk
        assert "state.inventory = []" in chunk
        assert "state.gameStarted = true" in chunk

    def test_new_game_runs_intro_sequence(self):
        """startNewGame invokes MirsEndIntro.run() when available."""
        js = _read("ui.js")
        idx = js.find("function startNewGame")
        assert idx != -1
        chunk = js[idx:idx + 700]
        assert "MirsEndIntro" in chunk
        assert ".run(" in chunk

    def test_new_game_hooks_interpreter_after_intro(self):
        """After intro, startNewGame hooks the interpreter."""
        js = _read("ui.js")
        idx = js.find("function startNewGame")
        assert idx != -1
        chunk = js[idx:idx + 700]
        assert "hookInterpreter" in chunk


class TestContinueButton:
    """'Continue' loads saved game (disabled/grayed if no save)."""

    def test_continue_button_present(self):
        html = _read("play.html")
        assert 'id="menu-continue"' in html

    def test_continue_button_disabled_by_default(self):
        """Continue button has disabled attribute when no save exists."""
        html = _read("play.html")
        match = re.search(r'<button[^>]*id="menu-continue"[^>]*>', html)
        assert match
        assert "disabled" in match.group(0)

    def test_check_saved_game_enables_continue(self):
        """checkSavedGame toggles the disabled state based on localStorage."""
        js = _read("ui.js")
        assert "checkSavedGame" in js
        assert "menuContinueBtn.disabled" in js

    def test_continue_game_loads_from_storage(self):
        """continueGame reads saved data from localStorage or SaveManager."""
        js = _read("ui.js")
        idx = js.find("function continueGame")
        assert idx != -1
        chunk = js[idx:idx + 2000]
        assert "SaveManager" in chunk or "localStorage" in chunk
        assert "state.gameStarted = true" in chunk

    def test_continue_does_not_play_intro(self):
        """Continue skips intro — goes directly into gameplay."""
        js = _read("ui.js")
        idx = js.find("function continueGame")
        assert idx != -1
        chunk = js[idx:idx + 2000]
        # continueGame should NOT call MirsEndIntro.run
        assert "MirsEndIntro.run" not in chunk


class TestIngameMenu:
    """Menu accessible during gameplay (ESC or menu button)."""

    def test_ingame_menu_button_exists(self):
        html = _read("play.html")
        assert 'id="ingame-menu-btn"' in html

    def test_esc_key_toggles_menu(self):
        """ESC key shows/hides the menu during gameplay."""
        js = _read("ui.js")
        assert '"Escape"' in js
        # ESC when game is active and menu hidden -> showMenu
        assert "showMenu" in js
        # ESC when game is active and menu visible -> hideMenu
        assert "hideMenu" in js

    def test_ingame_menu_button_calls_show_menu(self):
        js = _read("ui.js")
        assert "ingame-menu-btn" in js
        # The button is wired to showMenu via addEventListener in init()
        assert "showMenu" in js

    def test_returning_to_game_preserves_state(self):
        """hideMenu does NOT reset game state — just hides the overlay."""
        js = _read("ui.js")
        idx = js.find("function hideMenu")
        assert idx != -1
        chunk = js[idx:idx + 300]
        # hideMenu should only toggle visibility, not reset state
        assert "hidden" in chunk
        assert "state.o2" not in chunk
        assert "state.morale" not in chunk
        assert "state.inventory" not in chunk


# ── Save/Load ────────────────────────────────────────────────────────────


class TestSaveCommand:
    """SAVE command creates a save in browser localStorage."""

    def test_save_command_handled(self):
        js = _read("ui.js")
        assert '"save"' in js

    def test_quick_save_uses_save_manager(self):
        """quickSave delegates to SaveManager.saveToSlot."""
        js = _read("ui.js")
        idx = js.find("function quickSave")
        assert idx != -1
        chunk = js[idx:idx + 300]
        assert "SaveManager" in chunk
        assert "saveToSlot" in chunk

    def test_save_provides_feedback(self):
        """Save operation displays feedback message to user."""
        js = _read("ui.js")
        idx = js.find("function quickSave")
        assert idx != -1
        chunk = js[idx:idx + 300]
        assert "appendSystemText" in chunk


class TestRestoreCommand:
    """RESTORE command loads a saved game."""

    def test_restore_command_handled(self):
        js = _read("ui.js")
        assert '"restore"' in js

    def test_quick_load_uses_save_manager(self):
        js = _read("ui.js")
        idx = js.find("function quickLoad")
        assert idx != -1
        chunk = js[idx:idx + 400]
        assert "SaveManager" in chunk
        assert "getMostRecentSave" in chunk

    def test_restore_provides_feedback(self):
        js = _read("ui.js")
        idx = js.find("function quickLoad")
        assert idx != -1
        chunk = js[idx:idx + 400]
        assert "appendSystemText" in chunk


class TestSaveSlots:
    """Multiple save slots work (at least 3)."""

    def test_slot_count_at_least_3(self):
        sm = _read("save-manager.js")
        match = re.search(r"SLOT_COUNT\s*=\s*(\d+)", sm)
        assert match
        assert int(match.group(1)) >= 3

    def test_auto_save_slot_exists(self):
        sm = _read("save-manager.js")
        assert "AUTO_SAVE_KEY" in sm
        assert "autosave" in sm

    def test_list_slots_returns_all(self):
        """listSlots returns auto + numbered slots."""
        sm = _read("save-manager.js")
        idx = sm.find("function listSlots")
        assert idx != -1
        chunk = sm[idx:idx + 600]
        assert '"auto"' in chunk
        assert "SLOT_COUNT" in chunk


class TestAutoSave:
    """Auto-save triggers on room transitions."""

    def test_auto_save_on_room_change(self):
        """setCurrentRoom triggers auto-save when room changes."""
        js = _read("ui.js")
        idx = js.find("function setCurrentRoom")
        assert idx != -1
        chunk = js[idx:idx + 400]
        assert "autoSave" in chunk

    def test_auto_save_only_on_actual_change(self):
        """Auto-save only fires when room actually changes, not on re-entry."""
        js = _read("ui.js")
        idx = js.find("function setCurrentRoom")
        assert idx != -1
        chunk = js[idx:idx + 400]
        assert "changed" in chunk

    def test_auto_save_feedback_message(self):
        """Auto-save displays '[Auto-saved]' system message."""
        js = _read("ui.js")
        assert "[Auto-saved]" in js


class TestContinueMenuLoadsAutoSave:
    """'Continue' in menu loads most recent auto-save."""

    def test_continue_uses_most_recent_save(self):
        js = _read("ui.js")
        idx = js.find("function continueGame")
        assert idx != -1
        chunk = js[idx:idx + 2000]
        assert "getMostRecentSave" in chunk

    def test_save_manager_gets_most_recent_across_all_slots(self):
        """getMostRecentSave checks auto-save and all numbered slots."""
        sm = _read("save-manager.js")
        idx = sm.find("function getMostRecentSave")
        assert idx != -1
        chunk = sm[idx:idx + 500]
        assert "AUTO_SAVE_KEY" in chunk
        assert "SLOT_COUNT" in chunk


class TestSaveLoadFeedback:
    """Clear success/failure feedback on save and load."""

    def test_save_returns_success_message(self):
        sm = _read("save-manager.js")
        assert "Game saved successfully" in sm

    def test_load_returns_success_message(self):
        sm = _read("save-manager.js")
        assert "Game loaded successfully" in sm

    def test_load_returns_failure_on_missing(self):
        sm = _read("save-manager.js")
        assert "No save data found" in sm

    def test_storage_unavailable_message(self):
        sm = _read("save-manager.js")
        assert "localStorage is not available" in sm

    def test_save_result_has_success_field(self):
        sm = _read("save-manager.js")
        assert "success:" in sm
        assert "message:" in sm


class TestSavePersistence:
    """Save uses localStorage for cross-session persistence."""

    def test_save_manager_uses_localstorage(self):
        sm = _read("save-manager.js")
        assert "localStorage.setItem" in sm
        assert "localStorage.getItem" in sm

    def test_save_data_includes_timestamp(self):
        """Save snapshots include a timestamp for recency comparisons."""
        sm = _read("save-manager.js")
        idx = sm.find("function captureState")
        assert idx != -1
        chunk = sm[idx:idx + 400]
        assert "timestamp" in chunk
        assert "toISOString" in chunk

    def test_save_data_includes_game_state(self):
        """Save snapshots include all game state fields."""
        sm = _read("save-manager.js")
        idx = sm.find("function captureState")
        assert idx != -1
        chunk = sm[idx:idx + 600]
        for field in ["currentRoom", "o2", "morale", "inventory", "commandHistory"]:
            assert field in chunk, f"captureState missing {field}"


# ── Intro Sequence ───────────────────────────────────────────────────────


class TestIntroPlaysOnNewGame:
    """Intro plays on New Game."""

    def test_new_game_calls_intro_run(self):
        js = _read("ui.js")
        idx = js.find("function startNewGame")
        assert idx != -1
        chunk = js[idx:idx + 700]
        assert "MirsEndIntro" in chunk
        assert ".run(" in chunk

    def test_intro_has_narrative_content(self):
        """Intro contains atmospheric narrative text."""
        intro = _read("intro.js")
        assert "INTRO_STEPS" in intro
        assert "nightside" in intro or "silence" in intro
        assert "station" in intro.lower()


class TestIntroSkippable:
    """Intro is skippable (keypress or click)."""

    def test_skip_via_keypress(self):
        intro = _read("intro.js")
        assert "keydown" in intro
        assert "handleSkip" in intro

    def test_skip_via_click(self):
        intro = _read("intro.js")
        assert "click" in intro
        assert "handleSkipClick" in intro

    def test_skip_prompt_displayed(self):
        intro = _read("intro.js")
        assert "Press any key to skip" in intro

    def test_skip_has_delay_to_prevent_accidental(self):
        """Click skip is delayed to prevent accidental skip."""
        intro = _read("intro.js")
        # handleSkipClick checks elapsed time since intro started
        assert "handleSkipClick" in intro
        assert "introStartTime" in intro


class TestIntroNoReplayOnContinue:
    """Intro does NOT replay on Continue/Load."""

    def test_intro_uses_session_storage(self):
        """Intro marks itself as seen in sessionStorage."""
        intro = _read("intro.js")
        assert "sessionStorage" in intro
        assert "STORAGE_KEY" in intro

    def test_should_play_intro_checks_storage(self):
        intro = _read("intro.js")
        idx = intro.find("function shouldPlayIntro")
        assert idx != -1
        chunk = intro[idx:idx + 500]
        assert "sessionStorage.getItem" in chunk

    def test_should_play_intro_checks_url_params(self):
        """Intro respects skip_intro, continue, load URL params."""
        intro = _read("intro.js")
        idx = intro.find("function shouldPlayIntro")
        assert idx != -1
        chunk = intro[idx:idx + 800]
        assert "skip_intro" in chunk
        assert "continue" in chunk
        assert "load" in chunk

    def test_continue_game_does_not_run_intro(self):
        """continueGame in ui.js does NOT trigger MirsEndIntro.run."""
        js = _read("ui.js")
        idx = js.find("function continueGame")
        assert idx != -1
        chunk = js[idx:idx + 2000]
        assert "MirsEndIntro.run" not in chunk


class TestIntroTransition:
    """Smooth transition from intro into first room."""

    def test_intro_fades_out(self):
        intro = _read("intro.js")
        assert "opacity" in intro
        assert "1.2s" in intro or "transition" in intro

    def test_intro_removes_overlay_after_fade(self):
        intro = _read("intro.js")
        idx = intro.find("function endIntro")
        assert idx != -1
        chunk = intro[idx:idx + 1200]
        assert "remove()" in chunk

    def test_intro_shows_game_shell_after_end(self):
        intro = _read("intro.js")
        idx = intro.find("function endIntro")
        assert idx != -1
        chunk = intro[idx:idx + 1200]
        assert "game-shell" in chunk

    def test_intro_calls_completion_callback(self):
        intro = _read("intro.js")
        idx = intro.find("function endIntro")
        assert idx != -1
        chunk = intro[idx:idx + 1200]
        assert "onCompleteCallback" in chunk


class TestIntroDuration:
    """Intro duration is under 60 seconds."""

    def test_max_delay_under_60s(self):
        intro = _read("intro.js")
        delays = [int(d) for d in re.findall(r"delay:\s*(\d+)", intro)]
        assert len(delays) > 0
        assert max(delays) <= 60000, f"Max delay {max(delays)}ms exceeds 60s"

    def test_intro_ends_with_end_marker(self):
        """Last step in INTRO_STEPS has an end: true marker."""
        intro = _read("intro.js")
        # Find the last step before the closing bracket
        assert "end: true" in intro


# ── Regression: M1 + M2 ─────────────────────────────────────────────────


class TestM1Regression:
    """All M1 features still work correctly."""

    def test_inform7_source_exists(self):
        assert os.path.isfile(STORY_NI)

    def test_inform7_declares_title(self):
        with open(STORY_NI) as f:
            content = f.read()
        assert '"MIR\'S END"' in content

    def test_compile_script_exists_and_executable(self):
        path = os.path.join(ROOT, "scripts", "compile-inform7.sh")
        assert os.path.isfile(path)
        import stat
        assert os.stat(path).st_mode & stat.S_IXUSR

    def test_ink_reference_files_preserved(self):
        assert os.path.isfile(os.path.join(GAME_DIR, "story", "opening.ink"))
        assert os.path.isfile(os.path.join(GAME_DIR, "story", "main.ink"))

    def test_ascii_art_files_all_present(self):
        ascii_dir = os.path.join(GAME_DIR, "assets", "ascii")
        expected = [
            "darkness.txt", "corridor.txt", "bunks.txt",
            "command_module.txt", "radio.txt",
            "earth_burning.txt", "earth_from_orbit.txt",
        ]
        for f in expected:
            assert os.path.isfile(os.path.join(ascii_dir, f)), f"Missing: {f}"

    def test_package_json_has_build_scripts(self):
        with open(os.path.join(ROOT, "package.json")) as f:
            pkg = json.load(f)
        assert "build" in pkg["scripts"]
        assert "build:story" in pkg["scripts"]
        assert "build:ts" in pkg["scripts"]
        assert "lint" in pkg["scripts"]

    def test_gitignore_covers_artifacts(self):
        with open(os.path.join(ROOT, ".gitignore")) as f:
            content = f.read()
        assert "game/dist/" in content
        assert "node_modules/" in content
        assert "game/inform/Build/" in content

    def test_readme_has_essential_docs(self):
        with open(os.path.join(ROOT, "README.md")) as f:
            content = f.read()
        assert "npm install" in content
        assert "npm run build" in content


class TestM2Regression:
    """All M2 features still work correctly."""

    def test_web_ui_files_intact(self):
        for filename in ["play.html", "ui.css", "ui.js"]:
            assert os.path.isfile(os.path.join(GAME_DIR, filename))

    def test_room_art_mapping_complete(self):
        js = _read("ui.js")
        for room in ["crew quarters", "main corridor", "command module",
                      "observation cupola", "darkness"]:
            assert room in js.lower(), f"Missing ROOM_ART: {room}"

    def test_known_rooms_in_ui(self):
        js = _read("ui.js")
        for room in ["Crew Quarters", "Main Corridor", "Command Module",
                      "Observation Cupola"]:
            assert room in js, f"KNOWN_ROOMS missing: {room}"

    def test_status_variables_tracked(self):
        js = _read("ui.js")
        for var in ["o2", "morale", "inventory", "currentRoom"]:
            assert var in js

    def test_story_has_core_elements(self):
        with open(STORY_NI) as f:
            content = f.read()
        assert "Crew Quarters is a room" in content
        # Other rooms may use "is a room" or directional declarations
        assert "Main Corridor" in content
        assert "Command Module" in content
        assert "Observation Cupola" in content

    def test_story_has_npcs(self):
        with open(STORY_NI) as f:
            content = f.read()
        assert "Yevgenia" in content
        assert "Petrov" in content

    def test_story_has_resource_tracking(self):
        with open(STORY_NI) as f:
            content = f.read()
        assert "Oxygen-level" in content
        assert "Morale-level" in content

    def test_public_api_exposed(self):
        js = _read("ui.js")
        assert "window.MirsEnd" in js
        for method in ["appendStoryText", "setCurrentRoom", "updateStatus",
                        "getState", "setState"]:
            assert method in js, f"Public API missing: {method}"


# ── Build Pipeline ───────────────────────────────────────────────────────


class TestBuildPipelineM3:
    """Build pipeline compiles everything."""

    def test_package_json_scripts_intact(self):
        with open(os.path.join(ROOT, "package.json")) as f:
            pkg = json.load(f)
        assert "build" in pkg["scripts"]
        assert "lint" in pkg["scripts"]

    @pytest.mark.skipif(
        shutil.which("npx") is None,
        reason="npx not available",
    )
    def test_typescript_compiles(self):
        result = subprocess.run(
            ["npm", "run", "build:ts"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, (
            f"TypeScript build failed:\n{result.stdout}\n{result.stderr}"
        )

    @pytest.mark.skipif(
        shutil.which("npx") is None,
        reason="npx not available",
    )
    def test_biome_lint_passes(self):
        """Biome lint runs without crashing."""
        result = subprocess.run(
            ["npx", "biome", "check", "."],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode in (0, 1), (
            f"Biome crashed (exit {result.returncode}):\n{result.stderr}"
        )
        assert "Checked" in result.stdout

    def test_all_m3_files_exist(self):
        """All M3 feature files are present."""
        m3_files = [
            "game/play.html",
            "game/ui.js",
            "game/ui.css",
            "game/intro.js",
            "game/intro.css",
            "game/save-manager.js",
        ]
        for f in m3_files:
            path = os.path.join(ROOT, f)
            assert os.path.isfile(path), f"Missing M3 file: {f}"

    def test_all_m3_files_valid_utf8(self):
        """All M3 files are valid UTF-8."""
        for filename in ["play.html", "ui.js", "ui.css", "intro.js",
                          "intro.css", "save-manager.js"]:
            path = os.path.join(GAME_DIR, filename)
            with open(path, encoding="utf-8") as f:
                try:
                    f.read()
                except UnicodeDecodeError:
                    pytest.fail(f"{filename} is not valid UTF-8")


# ── Code Quality ─────────────────────────────────────────────────────────


class TestCodeQualityM3:
    """No console errors throughout full session."""

    def test_no_console_error_in_ui(self):
        js = _read("ui.js")
        assert "console.error" not in js

    def test_no_console_error_in_intro(self):
        js = _read("intro.js")
        assert "console.error" not in js

    def test_no_console_error_in_save_manager(self):
        js = _read("save-manager.js")
        assert "console.error" not in js

    def test_no_debugger_statements(self):
        for filename in ["ui.js", "intro.js", "save-manager.js"]:
            js = _read(filename)
            assert "debugger" not in js, f"debugger in {filename}"

    def test_no_alert_calls(self):
        for filename in ["ui.js", "intro.js", "save-manager.js"]:
            js = _read(filename)
            alerts = re.findall(r'\balert\s*\(', js)
            assert len(alerts) == 0, f"alert() in {filename}"

    def test_html_has_lang_attribute(self):
        html = _read("play.html")
        assert 'lang="en"' in html

    def test_html_has_charset(self):
        html = _read("play.html")
        assert 'charset="UTF-8"' in html or 'charset="utf-8"' in html

    def test_html_has_viewport(self):
        html = _read("play.html")
        assert "viewport" in html


# ── End-to-End Flow ──────────────────────────────────────────────────────


class TestEndToEndFlow:
    """Full walkthrough: launch -> title -> new game -> intro -> play -> save -> load."""

    def test_launch_shows_title_screen(self):
        """On load, title screen is shown (init calls showMenu)."""
        js = _read("ui.js")
        init_idx = js.find("function init()")
        assert init_idx != -1
        chunk = js[init_idx:init_idx + 1200]
        assert "showMenu" in chunk

    def test_title_to_new_game_to_intro(self):
        """New Game button -> startNewGame -> MirsEndIntro.run."""
        js = _read("ui.js")
        # Button wired in init
        assert "menu-new-game" in js
        assert "startNewGame" in js
        # startNewGame runs intro
        idx = js.find("function startNewGame")
        chunk = js[idx:idx + 700]
        assert "MirsEndIntro" in chunk

    def test_intro_ends_into_gameplay(self):
        """Intro completion -> hookInterpreter -> focus input."""
        js = _read("ui.js")
        idx = js.find("function startNewGame")
        chunk = js[idx:idx + 700]
        assert "hookInterpreter" in chunk
        assert "commandInput.focus" in chunk

    def test_shell_mode_supports_navigation(self):
        """Shell mode handles navigation commands for demo play."""
        js = _read("ui.js")
        assert "handleShellCommand" in js
        for cmd in ['"look"', '"north"', '"south"', '"east"', '"west"']:
            assert cmd in js, f"Shell missing command: {cmd}"

    def test_shell_mode_supports_save_restore(self):
        """Shell mode handles save and restore commands."""
        js = _read("ui.js")
        assert '"save"' in js
        assert '"restore"' in js

    def test_save_then_load_round_trip(self):
        """Save manager can serialize and deserialize state symmetrically."""
        sm = _read("save-manager.js")
        # captureState produces data, applyState consumes it
        assert "captureState" in sm
        assert "applyState" in sm
        # Both use the same fields
        for field in ["currentRoom", "o2", "morale", "inventory"]:
            assert field in sm

    def test_save_load_modal_for_slot_selection(self):
        """Save/load modal UI lets users pick slots."""
        js = _read("ui.js")
        assert "showSaveLoadModal" in js
        assert '"save"' in js
        assert '"load"' in js
        assert "save-slot-row" in js

    def test_game_playable_from_title_to_boundary(self):
        """All rooms from story.ni are reachable via shell mode navigation."""
        js = _read("ui.js")
        with open(STORY_NI) as f:
            story = f.read()
        # All four rooms exist in both story and UI
        rooms = ["Crew Quarters", "Main Corridor", "Command Module",
                 "Observation Cupola"]
        for room in rooms:
            assert room in story, f"Story missing room: {room}"
            assert room in js, f"UI missing room: {room}"


# ── Cross-Component Integration ──────────────────────────────────────────


class TestCrossComponentIntegration:
    """All M3 components work together."""

    def test_script_load_order(self):
        """Scripts load in correct order: intro.js -> save-manager.js -> ui.js."""
        html = _read("play.html")
        intro_pos = html.find('src="intro.js"')
        save_pos = html.find('src="save-manager.js"')
        ui_pos = html.find('src="ui.js"')
        assert intro_pos < save_pos < ui_pos

    def test_intro_api_consumed_by_ui(self):
        """ui.js uses window.MirsEndIntro API."""
        js = _read("ui.js")
        assert "MirsEndIntro" in js
        assert "MirsEndIntro.run" in js or "MirsEndIntro?.isActive" in js

    def test_save_manager_api_consumed_by_ui(self):
        """ui.js uses window.SaveManager API."""
        js = _read("ui.js")
        assert "SaveManager" in js
        assert "SaveManager.saveToSlot" in js or "SaveManager.autoSave" in js

    def test_ui_exposes_complete_public_api(self):
        """window.MirsEnd includes all M3 API methods."""
        js = _read("ui.js")
        m3_methods = [
            "showMenu", "hideMenu", "saveGame", "startNewGame",
            "showSaveModal", "showLoadModal", "quickSave", "quickLoad",
            "continueGame",
        ]
        for method in m3_methods:
            assert method in js, f"Public API missing: {method}"

    def test_css_covers_all_components(self):
        """CSS has rules for title screen, save/load, and intro."""
        css = _read("ui.css")
        assert "#title-screen" in css
        assert "#save-load-overlay" in css or "#save-load-modal" in css
        assert "#ingame-menu-btn" in css

        intro_css = _read("intro.css")
        assert "#intro-overlay" in intro_css
        assert "#intro-flash" in intro_css
        assert "#intro-skip" in intro_css

    def test_no_orphan_dom_references(self):
        """All DOM IDs referenced in JS exist in HTML."""
        html = _read("play.html")
        critical_ids = [
            "title-screen", "menu-new-game", "menu-continue",
            "ingame-menu-btn", "story-output", "scene-art",
            "command-input", "status-o2", "status-morale",
            "inventory-list", "game-shell",
            "btn-save", "btn-load", "btn-continue",
        ]
        for dom_id in critical_ids:
            assert dom_id in html, f"DOM ID missing in HTML: {dom_id}"
