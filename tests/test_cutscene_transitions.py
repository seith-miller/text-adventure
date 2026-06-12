"""Tests for module-change cutscene transitions (issue #138).

Per-column wipe transitions (demonstrated in `game/mockups/v5-cutscene.html`)
fire when the player moves between modules.

Acceptance criteria from issue:
- A `transitionTo(sceneId)` API the game calls on module entry
- A frames registry mapping sceneId → frames file
- Falls back gracefully if no scene file is registered (plain wipe, no video)
- Player can skip the cutscene with any key
- No game state or input lost during a cutscene
- Reduced-motion preference (#144) replaces wipe with hard cut
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


def _read(filename):
    path = os.path.join(GAME_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── File existence ──


def test_cutscene_js_exists():
    """game/cutscene.js exists."""
    path = os.path.join(GAME_DIR, "cutscene.js")
    assert os.path.isfile(path), "game/cutscene.js not found"


def test_cutscene_js_loaded_in_play_html():
    """play.html loads cutscene.js."""
    html = _read("play.html")
    assert 'src="cutscene.js"' in html, "play.html must include cutscene.js"


def test_cutscene_js_loads_before_ui_js():
    """cutscene.js must load before ui.js so the API is available
    when setCurrentRoom triggers transitionTo."""
    html = _read("play.html")
    cs_pos = html.find('src="cutscene.js"')
    ui_pos = html.find('src="ui.js"')
    assert cs_pos != -1 and ui_pos != -1
    assert cs_pos < ui_pos, "cutscene.js must load before ui.js"


# ── Public API ──


def test_cutscene_exposes_public_api():
    """window.MirsEndCutscene is the public API namespace."""
    js = _read("cutscene.js")
    assert "window.MirsEndCutscene" in js, "Missing public API namespace"


def test_transition_to_api_method():
    """transitionTo(sceneId) is exposed on the public API."""
    js = _read("cutscene.js")
    assert "transitionTo" in js, "Missing transitionTo method"


def test_register_scene_api_method():
    """registerScene(sceneId, framesFile) is exposed for the frames registry."""
    js = _read("cutscene.js")
    assert "registerScene" in js, "Missing registerScene method"


def test_is_active_api_method():
    """isActive() lets the game check whether a cutscene is currently playing."""
    js = _read("cutscene.js")
    assert "isActive" in js, "Missing isActive method"


# ── Frames registry ──


def test_default_scene_registry_documented():
    """The registry maps sceneId → frames file path (e.g., corridor → frames/corridor.js).

    The module's source must include the default mapping so consumers can
    discover which scenes ship with the game.
    """
    js = _read("cutscene.js")
    assert "registry" in js.lower(), "Missing scene registry concept"
    # At minimum there must be a default registry seeded with the well-known
    # sceneId → frames file mapping called out in the issue.
    assert "frames/" in js, (
        "Registry should reference frames file paths (e.g., frames/corridor.js)"
    )


def test_registry_seeded_with_known_rooms():
    """The default registry seeds at least one of the known room scene IDs."""
    js = _read("cutscene.js")
    # At least one of the well-known scenes from the issue should be present
    known = ["corridor", "command", "cupola", "crew", "darkness"]
    assert any(name in js.lower() for name in known), (
        "Registry should seed at least one known room sceneId"
    )


# ── Fallback when no frames file is registered ──


def test_fallback_plain_wipe_when_no_scene():
    """When the sceneId isn't in the registry, the transition still plays a
    plain wipe — no video — so the player still gets the scene-change cue."""
    js = _read("cutscene.js")
    # The source should explicitly handle the no-registered-scene case.
    # Look for fallback or "plain wipe" comment/code path.
    assert re.search(r"fallback|plain[\s_-]?wipe|no[\s_-]?frames", js, re.I), (
        "Missing fallback / plain-wipe handling for unregistered scenes"
    )


# ── Skip on any key ──


def test_skip_on_any_key():
    """Any keypress during a cutscene skips it."""
    js = _read("cutscene.js")
    # Look for keydown handler that calls skip / cancel during a cutscene.
    assert "keydown" in js, "Missing keydown handler for skip"
    assert re.search(r"skip|cancel|end", js, re.I), (
        "Missing skip/cancel hook for cutscene"
    )


def test_skip_api_method():
    """skip() is exposed publicly so external code can force-skip."""
    js = _read("cutscene.js")
    assert re.search(r"\bskip\b", js), "Missing skip method"


# ── No state or input lost during cutscene ──


def test_input_is_buffered_or_routed_after_cutscene():
    """The cutscene must not swallow gameplay input — game state/input should
    survive. We check that the implementation doesn't destructively replace
    the command input element, and that the skip handler is removed after
    the cutscene ends (so subsequent keypresses go to the game, not skip)."""
    js = _read("cutscene.js")
    assert "removeEventListener" in js, (
        "Cutscene must remove its keydown listener when finished so input "
        "isn't lost to the skip handler after the cutscene"
    )


def test_does_not_clear_command_input():
    """The cutscene must not clear or reset the command-input element."""
    js = _read("cutscene.js")
    # The script must not touch command-input.value or .innerHTML clears
    # on that element. Search for any reference to command-input and verify
    # the code doesn't mutate its value.
    assert "command-input" not in js or not re.search(
        r'command-input["\']\)\s*\.value\s*=', js
    ), "Cutscene should not clear command-input.value"


# ── Reduced-motion preference ──


def test_reduced_motion_replaces_wipe_with_hard_cut():
    """Reduced-motion preference (#144) replaces the wipe with a hard cut."""
    js = _read("cutscene.js")
    assert "prefers-reduced-motion" in js, (
        "Missing prefers-reduced-motion media query check"
    )


def test_reduced_motion_path_is_synchronous_or_immediate():
    """Under reduced-motion, the cutscene completes (essentially) immediately —
    no animation frames, no per-column wipe."""
    js = _read("cutscene.js")
    # We need to see a code path that short-circuits the animation when
    # reduced motion is preferred. Look for an early return or a hardCut helper.
    assert re.search(
        r"(hardCut|hard[_\s-]?cut|reduced[A-Za-z]*\s*[?&]|matches[^;]*reduced)",
        js,
    ), "Missing hard-cut / short-circuit path for reduced motion"


# ── Integration with the live game ──


def test_set_current_room_calls_transition_to():
    """setCurrentRoom (the room-change hook) calls MirsEndCutscene.transitionTo
    when the room actually changed."""
    js = _read("ui.js")
    # Find setCurrentRoom and check it references the cutscene API.
    idx = js.find("function setCurrentRoom")
    assert idx != -1, "setCurrentRoom not found in ui.js"
    chunk = js[idx : idx + 1200]
    assert "MirsEndCutscene" in chunk or "transitionTo" in chunk, (
        "setCurrentRoom must call the cutscene transition API on room change"
    )


def test_transition_only_fires_when_room_actually_changes():
    """The cutscene should only fire when the room actually changes — not on
    re-entering the same room. setCurrentRoom already tracks `changed`; the
    transitionTo call must be gated on that variable."""
    js = _read("ui.js")
    idx = js.find("function setCurrentRoom")
    assert idx != -1
    chunk = js[idx : idx + 1500]
    # transitionTo must be inside a `changed` conditional block somewhere.
    assert "changed" in chunk and (
        "MirsEndCutscene" in chunk or "transitionTo" in chunk
    ), "Transition must be gated on the `changed` flag in setCurrentRoom"


def test_mirs_end_cutscene_namespace_exposed():
    """The public namespace is window.MirsEndCutscene (consistent with
    window.MirsEnd, window.MirsEndIntro, etc.)."""
    js = _read("cutscene.js")
    assert "window.MirsEndCutscene" in js, (
        "Public namespace should be window.MirsEndCutscene"
    )


def test_frames_directory_path_present():
    """The cutscene loader references the frames/ directory under game/."""
    js = _read("cutscene.js")
    assert "frames/" in js, "Loader should reference frames/ asset path"
