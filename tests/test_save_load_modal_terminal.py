"""Tests for the v3 terminal-aesthetic save/load modal (issue #137).

Verifies that the save/load modal:
  - frames itself with box-drawing characters (╔ ═ ╗ ║ ╚ ╝)
  - labels slots bilingually (e.g. ``SLOT 01 / СЛОТ 01``)
  - uses the terminal-button style (uppercase, letter-spaced, phosphor hover)
  - closes on Escape
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── Box-drawing frame ──


def test_ui_js_emits_box_drawing_frame():
    """The save/load modal frame uses Unicode box-drawing characters."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # The four corners of a heavy/double box frame.
    for ch in ("╔", "╗", "╚", "╝"):
        assert ch in content, (
            f"ui.js should emit the {ch!r} box-drawing corner for "
            "the save/load modal frame"
        )
    # And the horizontal/vertical edges.
    for ch in ("═", "║"):
        assert ch in content, (
            f"ui.js should emit the {ch!r} box-drawing edge for "
            "the save/load modal frame"
        )


def test_ui_css_modal_has_box_frame_class():
    """The modal pre/frame is styled as a monospace block so the
    box-drawing characters align."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # A frame block (e.g. .save-load-frame or #save-load-modal pre) carries
    # white-space: pre + IBM Plex Mono so the corners stay aligned.
    frame_block = re.search(
        r"(\.save-load-frame|#save-load-modal\s+pre|\.save-load-box)"
        r"[^{]*\{[^}]*?white-space\s*:\s*pre",
        content,
        re.DOTALL,
    )
    assert frame_block, (
        "ui.css should have a save-load frame selector with white-space: pre"
    )


# ── Bilingual slot labels ──


def test_ui_js_renders_bilingual_slot_labels():
    """Each numbered slot label includes the Russian shadow `СЛОТ NN`."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    assert "СЛОТ" in content, (
        "Slot labels should carry the Cyrillic shadow `СЛОТ`"
    )
    # The English label is `SLOT NN`. We expect zero-padded slot numbers in
    # the visual label (matches the v3 mockup of `SLOT 01 / СЛОТ 01`).
    assert re.search(r"SLOT\s*\$\{[^}]*\}|SLOT\s*0?1", content), (
        "Slot labels should include `SLOT NN` text"
    )


def test_ui_js_renders_bilingual_autosave_label():
    """The auto-save slot also gets a Cyrillic shadow."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    assert "АВТО" in content, (
        "Auto-save slot label should include the Cyrillic `АВТО`"
    )


# ── Terminal button style ──


def test_ui_css_save_slot_btn_uses_phosphor_hover():
    """Save/Load/Cancel buttons hover to phosphor green, not the legacy
    accent-cyan from the pre-v3 modal."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Find the .save-slot-btn:hover rule body.
    hover = re.search(
        r"\.save-slot-btn:hover\s*\{([^}]*)\}",
        content,
        re.DOTALL,
    )
    assert hover, "Missing .save-slot-btn:hover rule"
    assert "--phosphor" in hover.group(1), (
        "save-slot-btn hover should use --phosphor (terminal phosphor green)"
    )


def test_ui_css_close_btn_uses_phosphor_hover():
    """The Cancel/Close button hovers to phosphor as well."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    hover = re.search(
        r"#save-load-close:hover\s*\{([^}]*)\}",
        content,
        re.DOTALL,
    )
    assert hover, "Missing #save-load-close:hover rule"
    assert "--phosphor" in hover.group(1), (
        "save/load close button hover should use --phosphor"
    )


def test_ui_css_modal_buttons_are_uppercase_letterspaced():
    """The Save/Load/Cancel buttons match the terminal button style:
    uppercase + letter-spaced (already true for save-slot-btn, must remain)."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    btn = re.search(
        r"\.save-slot-btn\s*\{([^}]*)\}",
        content,
        re.DOTALL,
    )
    assert btn, "Missing .save-slot-btn rule"
    assert "text-transform" in btn.group(1) and "uppercase" in btn.group(1), (
        "save-slot-btn should be uppercase"
    )
    assert "letter-spacing" in btn.group(1), (
        "save-slot-btn should be letter-spaced"
    )

    close = re.search(
        r"#save-load-close\s*\{([^}]*)\}",
        content,
        re.DOTALL,
    )
    assert close, "Missing #save-load-close rule"
    assert (
        "text-transform" in close.group(1) and "uppercase" in close.group(1)
    ), "save-load close button should be uppercase"
    assert "letter-spacing" in close.group(1), (
        "save-load close button should be letter-spaced"
    )


# ── Escape closes the modal ──


def test_ui_js_escape_closes_save_load_modal():
    """Pressing Escape while the modal is open closes it (and does NOT
    fall through to the in-game menu)."""
    path = os.path.join(GAME_DIR, "ui.js")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # The ESC handler must check for the open modal before toggling the menu.
    esc_handler = re.search(
        r'e\.key\s*===\s*"Escape"\s*\)\s*\{(.*?)\n\s{4,6}\}\s*\}\)',
        content,
        re.DOTALL,
    )
    assert esc_handler, "Could not locate the ESC keydown handler"
    body = esc_handler.group(1)
    # Either the handler references closeSaveLoadModal or it consults the
    # _saveLoadModalOpen flag.
    assert (
        "closeSaveLoadModal" in body or "_saveLoadModalOpen" in body
    ), "ESC handler should close the save/load modal before doing anything else"


# ── Modal uses terminal font stack ──


def test_ui_css_modal_uses_ibm_plex_mono():
    """The modal body uses IBM Plex Mono (v3 terminal font)."""
    path = os.path.join(GAME_DIR, "ui.css")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    modal = re.search(
        r"#save-load-modal\s*\{([^}]*)\}",
        content,
        re.DOTALL,
    )
    assert modal, "Missing #save-load-modal rule"
    assert "IBM Plex Mono" in modal.group(1), (
        "save-load modal should use IBM Plex Mono"
    )
