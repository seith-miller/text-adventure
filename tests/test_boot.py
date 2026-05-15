"""Tests for the Soviet POST-style boot sequence (issue #136)."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "game")


# ── File existence ──


def test_boot_js_exists():
    """boot.js exists in the game directory."""
    path = os.path.join(GAME_DIR, "boot.js")
    assert os.path.isfile(path), "game/boot.js not found"


def test_boot_css_exists():
    """boot.css exists in the game directory."""
    path = os.path.join(GAME_DIR, "boot.css")
    assert os.path.isfile(path), "game/boot.css not found"


# ── HTML integration ──


def test_play_html_loads_boot_js():
    """play.html includes the boot.js script."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'src="boot.js"' in content, "boot.js not referenced in play.html"


def test_play_html_loads_boot_css():
    """play.html includes the boot.css stylesheet."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert 'href="boot.css"' in content, "boot.css not referenced in play.html"


def test_boot_js_loads_before_ui_js():
    """boot.js is loaded before ui.js so the API is available."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    boot_pos = content.find('src="boot.js"')
    ui_pos = content.find('src="ui.js"')
    assert boot_pos != -1, "boot.js not found in play.html"
    assert ui_pos != -1, "ui.js not found in play.html"
    assert boot_pos < ui_pos, "boot.js must load before ui.js"


def test_boot_js_loads_before_intro_js():
    """boot.js loads before intro.js (boot runs first on page load)."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    boot_pos = content.find('src="boot.js"')
    intro_pos = content.find('src="intro.js"')
    assert boot_pos != -1, "boot.js not found in play.html"
    assert intro_pos != -1, "intro.js not found in play.html"
    assert boot_pos < intro_pos, "boot.js must load before intro.js"


# ── Boot sequence content ──


def test_boot_has_cyrillic_text():
    """Boot lines include Cyrillic characters for Soviet aesthetic."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    # Check for Cyrillic characters (basic range U+0400–U+04FF)
    assert re.search(r"[\u0400-\u04FF]", content), (
        "Missing Cyrillic text in boot lines"
    )


def test_boot_has_english_text():
    """Boot lines include English/Latin text."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "OK" in content, "Missing OK status in boot lines"
    assert "NOMINAL" in content or "ACK" in content, (
        "Missing technical status text"
    )


def test_boot_has_station_reference():
    """Boot sequence references the MIR station."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "MIR" in content, "Missing MIR station reference"


def test_boot_has_ready_line():
    """Boot sequence ends with a READY / ГОТОВ line."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "READY" in content, "Missing READY text"
    assert "ГОТОВ" in content, "Missing ГОТОВ (Russian READY) text"


def test_boot_has_6_to_12_lines():
    """Boot sequence has 6–12 POST lines (not counting READY)."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    # Count items in the BOOT_LINES array
    lines = re.findall(r'"[^"]*(?:OK|NOMINAL|ACK|LOCK|DEGRADED|v\d)[^"]*"', content)
    assert 6 <= len(lines) <= 12, (
        f"Expected 6–12 boot lines, found {len(lines)}"
    )


def test_boot_has_mixed_status_values():
    """Boot lines show variety in status values (not all OK)."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    statuses = set()
    for status in ["OK", "NOMINAL", "ACK", "LOCK", "DEGRADED"]:
        if status in content:
            statuses.add(status)
    assert len(statuses) >= 3, (
        f"Boot lines should have varied status values, found: {statuses}"
    )


# ── Timing ──


def test_boot_line_interval_in_range():
    """Line interval is between 150–300ms per acceptance criteria."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    match = re.search(r"LINE_INTERVAL\s*=\s*(\d+)", content)
    assert match, "Missing LINE_INTERVAL constant"
    interval = int(match.group(1))
    assert 150 <= interval <= 300, (
        f"LINE_INTERVAL {interval}ms outside 150–300ms range"
    )


def test_boot_total_duration_around_2_seconds():
    """Boot sequence total duration is roughly ~2 seconds."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    interval_match = re.search(r"LINE_INTERVAL\s*=\s*(\d+)", content)
    ready_pause_match = re.search(r"READY_PAUSE\s*=\s*(\d+)", content)
    hold_match = re.search(r"HOLD_AFTER_READY\s*=\s*(\d+)", content)
    assert interval_match and ready_pause_match and hold_match, (
        "Missing timing constants"
    )
    # Count boot lines
    lines = re.findall(r'"[^"]*(?:OK|NOMINAL|ACK|LOCK|DEGRADED|v\d)[^"]*"', content)
    interval = int(interval_match.group(1))
    ready_pause = int(ready_pause_match.group(1))
    hold = int(hold_match.group(1))
    total = len(lines) * interval + ready_pause + hold
    assert 1500 <= total <= 4000, (
        f"Total boot duration {total}ms should be roughly ~2 seconds"
    )


# ── Skippable ──


def test_boot_is_skippable_by_key():
    """Boot registers a keydown listener for skipping."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "keydown" in content, "Missing keydown listener for skip"


def test_boot_is_skippable_by_click():
    """Boot registers a click listener for skipping."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "click" in content, "Missing click listener for skip"


def test_boot_has_skip_prompt():
    """Boot displays a skip prompt."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "skip" in content.lower(), "Missing skip prompt"


# ── CSS styling ──


def test_boot_overlay_is_fullscreen():
    """Boot overlay covers the full viewport."""
    path = os.path.join(GAME_DIR, "boot.css")
    with open(path) as f:
        content = f.read()
    assert "position: fixed" in content, "Overlay must be fixed position"
    assert "width: 100%" in content, "Overlay must cover full width"
    assert "height: 100%" in content, "Overlay must cover full height"
    assert "z-index" in content, "Overlay must have z-index"


def test_boot_css_has_line_styling():
    """Boot CSS defines styles for POST lines."""
    path = os.path.join(GAME_DIR, "boot.css")
    with open(path) as f:
        content = f.read()
    assert ".boot-line" in content, "Missing boot-line class"
    assert ".visible" in content, "Missing visibility state"


def test_boot_css_has_ready_styling():
    """Boot CSS has distinct styling for the READY line."""
    path = os.path.join(GAME_DIR, "boot.css")
    with open(path) as f:
        content = f.read()
    assert ".boot-ready" in content, "Missing boot-ready class"


def test_boot_css_has_monospace_font():
    """Boot uses monospace font for terminal aesthetic."""
    path = os.path.join(GAME_DIR, "boot.css")
    with open(path) as f:
        content = f.read()
    assert "Courier" in content or "monospace" in content, (
        "Missing monospace font"
    )


def test_boot_css_has_skip_styling():
    """CSS includes styling for the skip prompt."""
    path = os.path.join(GAME_DIR, "boot.css")
    with open(path) as f:
        content = f.read()
    assert "boot-skip" in content, "Missing skip prompt styling"


def test_boot_css_has_cursor_animation():
    """Boot CSS includes a blinking cursor animation."""
    path = os.path.join(GAME_DIR, "boot.css")
    with open(path) as f:
        content = f.read()
    assert "boot-cursor" in content, "Missing cursor element"
    assert "@keyframes" in content, "Missing cursor animation keyframes"


# ── Transition ──


def test_boot_transitions_to_title_screen():
    """Boot ends by showing the title screen."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "title-screen" in content, (
        "Missing title-screen reference for transition"
    )
    assert "onCompleteCallback" in content or "callback" in content, (
        "Missing completion callback"
    )


def test_boot_overlay_fades_out():
    """Boot overlay fades out rather than disappearing abruptly."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "opacity" in content, "Missing opacity transition for fade-out"


def test_boot_does_not_block_glulx():
    """Boot sequence doesn't call MirsEndBoot.start() — it runs in parallel."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    # boot.js should not directly start the interpreter
    assert "MirsEndBoot.start" not in content, (
        "boot.js should not call MirsEndBoot.start — boot runs in parallel"
    )
    assert "GiLoad" not in content, (
        "boot.js should not reference GiLoad — it's purely visual"
    )


# ── Public API ──


def test_boot_exposes_public_api():
    """Boot exposes a window.MirsEndBoot_POST public API."""
    path = os.path.join(GAME_DIR, "boot.js")
    with open(path) as f:
        content = f.read()
    assert "window.MirsEndBoot_POST" in content, "Missing public API"
    assert "run" in content, "API missing run method"
    assert "skip" in content, "API missing skip method"
    assert "isActive" in content, "API missing isActive method"


# ── play.html integration ──


def test_play_html_starts_boot_on_load():
    """play.html starts the boot sequence on DOMContentLoaded."""
    path = os.path.join(GAME_DIR, "play.html")
    with open(path) as f:
        content = f.read()
    assert "MirsEndBoot_POST" in content, (
        "play.html does not reference MirsEndBoot_POST"
    )
    assert "DOMContentLoaded" in content, (
        "Boot must start on DOMContentLoaded"
    )
    assert "MirsEndBoot_POST.run" in content, (
        "play.html does not call MirsEndBoot_POST.run"
    )
