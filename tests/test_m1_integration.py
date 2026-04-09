"""M1 integration tests — Inform 7 Foundation pipeline verification.

These tests gate the M1 milestone. They verify that:
  1. The Inform 7 build pipeline produces a Glulx story file
  2. A clean rebuild (with Build/dist removed) succeeds
  3. The build script fails clearly on invalid source
  4. The compiled story loads in glulxe and supports basic parser commands
  5. No regression in existing tests (lint, package metadata)

The interactive story tests require `glulxe` on PATH. They are skipped (not
failed) when glulxe is not installed, so the suite still runs in environments
that only have the build toolchain.

See tests/INTEGRATION_TESTS.md for the manual smoke checks that complement
this automated suite.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from glulxe_driver import have_glulxe, normalize, run_glulxe

ROOT = Path(__file__).resolve().parent.parent
STORY_SOURCE = ROOT / "game" / "inform" / "Source" / "story.ni"
STORY_OUTPUT = ROOT / "game" / "dist" / "story.ulx"
DIST_DIR = ROOT / "game" / "dist"
INFORM_BUILD_DIR = ROOT / "game" / "inform" / "Build"
COMPILE_SCRIPT = ROOT / "scripts" / "compile-inform7.sh"


def _have_inform_compiler() -> bool:
    """Return True if the Inform 7 toolchain is reachable."""
    if shutil.which("inbuild") or shutil.which("inform7"):
        return True
    if os.environ.get("INFORM7_HOME") or os.environ.get("INFORM7_COMPILER"):
        return True
    return False


needs_compiler = pytest.mark.skipif(
    not _have_inform_compiler(),
    reason="Inform 7 toolchain not available (set INFORM7_HOME or install inbuild)",
)
needs_glulxe = pytest.mark.skipif(
    not have_glulxe(),
    reason="glulxe interpreter not available",
)
needs_compiled_story = pytest.mark.skipif(
    not STORY_OUTPUT.is_file(),
    reason="game/dist/story.ulx not present — run `npm run build:story` first",
)


# ─────────────────────────────────────────────────────────────────────────────
# Build pipeline
# ─────────────────────────────────────────────────────────────────────────────


def test_compile_script_is_executable():
    """The compile script exists and is marked executable."""
    assert COMPILE_SCRIPT.is_file(), f"missing {COMPILE_SCRIPT}"
    assert os.access(COMPILE_SCRIPT, os.X_OK), "compile-inform7.sh is not executable"


def test_story_source_exists_and_declares_title():
    """The Inform 7 source file exists and declares MIR'S END."""
    assert STORY_SOURCE.is_file(), f"missing {STORY_SOURCE}"
    text = STORY_SOURCE.read_text()
    assert '"MIR\'S END"' in text, "title declaration missing from story.ni"


@needs_compiled_story
def test_compiled_story_exists():
    """A compiled .ulx exists in game/dist (build:story has been run)."""
    assert STORY_OUTPUT.is_file(), (
        f"{STORY_OUTPUT} not found — run `npm run build:story` first"
    )


@needs_compiled_story
def test_compiled_story_has_glulx_magic_header():
    """The .ulx file starts with the Glulx magic number 'Glul'."""
    with STORY_OUTPUT.open("rb") as f:
        magic = f.read(4)
    assert magic == b"Glul", f"unexpected magic header: {magic!r}"


@needs_compiled_story
def test_compiled_story_is_nontrivial_size():
    """A successful compile produces a story file larger than a stub."""
    size = STORY_OUTPUT.stat().st_size
    # The minimal Inform 7 game compiles to ~600 KB. Anything below 200 KB
    # is almost certainly a broken/stub build.
    assert size > 200_000, f"story.ulx is suspiciously small ({size} bytes)"


@needs_compiler
def test_clean_rebuild_succeeds():
    """Deleting Build/ and dist/ then rebuilding produces a fresh .ulx."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if INFORM_BUILD_DIR.exists():
        shutil.rmtree(INFORM_BUILD_DIR)

    result = subprocess.run(
        ["npm", "run", "build:story"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"build:story failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert STORY_OUTPUT.is_file(), "build:story did not produce story.ulx"
    with STORY_OUTPUT.open("rb") as f:
        assert f.read(4) == b"Glul"


@needs_compiler
def test_build_script_fails_on_invalid_source(tmp_path):
    """The build script returns non-zero when given a malformed source."""
    backup = STORY_SOURCE.read_text()
    bad_source = (
        '"BROKEN BUILD" by "Test"\n\n'
        "This is not valid Inform 7 syntax — sentences must form rules,\n"
        "rooms, or things, and this paragraph forms none of those.\n"
        "Floob the wibble unto the wobble.\n"
    )
    try:
        STORY_SOURCE.write_text(bad_source)
        result = subprocess.run(
            ["bash", str(COMPILE_SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert result.returncode != 0, (
            "compile-inform7.sh succeeded on invalid source — expected failure"
        )
    finally:
        STORY_SOURCE.write_text(backup)
        # Restore a known-good build so later tests are not poisoned
        subprocess.run(
            ["npm", "run", "build:story"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Story behavior (requires glulxe)
# ─────────────────────────────────────────────────────────────────────────────


@needs_glulxe
@needs_compiled_story
def test_story_loads_and_shows_title():
    """Launching the story shows the title and the Crew Quarters room."""
    output = normalize(run_glulxe(str(STORY_OUTPUT), ["quit"]))
    assert "MIR'S END" in output, "title screen text not found"
    assert "Crew Quarters" in output, "starting room not displayed"


@needs_glulxe
@needs_compiled_story
def test_story_responds_to_look():
    """LOOK reprints the current room description."""
    output = normalize(run_glulxe(str(STORY_OUTPUT), ["look", "quit"]))
    assert "sleeping bay of Mir-2" in output, (
        "LOOK did not return the Crew Quarters description"
    )
    assert "main corridor lies to the north" in output


@needs_glulxe
@needs_compiled_story
def test_story_supports_object_interaction():
    """The player can OPEN and EXAMINE the emergency locker."""
    output = normalize(
        run_glulxe(
            str(STORY_OUTPUT),
            ["open emergency locker", "examine emergency locker", "quit"],
        )
    )
    assert "open the emergency locker" in output, "open verb did not fire"
    assert "chemical flashlight" in output, "flashlight not revealed inside locker"


@needs_glulxe
@needs_compiled_story
def test_story_supports_navigation():
    """The player can move from Crew Quarters to the Main Corridor."""
    output = normalize(run_glulxe(str(STORY_OUTPUT), ["n", "quit"]))
    assert "Main Corridor" in output, "navigation north did not reach Main Corridor"
    assert "command module is to the north" in output, (
        "Main Corridor description not displayed after navigation"
    )


@needs_glulxe
@needs_compiled_story
def test_story_quit_exits_cleanly():
    """The QUIT verb followed by Y produces the 'Hit any key to exit.' prompt."""
    output = normalize(run_glulxe(str(STORY_OUTPUT), ["quit"]))
    assert "Are you sure you want to quit?" in output
    assert "Hit any key to exit" in output


# ─────────────────────────────────────────────────────────────────────────────
# Regression
# ─────────────────────────────────────────────────────────────────────────────


def test_package_json_declares_build_story():
    """package.json still wires npm run build:story to the Inform 7 script."""
    import json

    pkg = json.loads((ROOT / "package.json").read_text())
    assert "build:story" in pkg["scripts"]
    assert "compile-inform7" in pkg["scripts"]["build:story"]


def test_biome_lint_passes():
    """Biome lint passes on the JS/TS sources (regression for CI workflow)."""
    npx = shutil.which("npx") or shutil.which("npm")
    if npx is None:
        pytest.skip("npx/npm not available")
    result = subprocess.run(
        ["npx", "biome", "check", "."],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"biome check failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_node_dependencies_intact():
    """node_modules is populated and inkjs (still referenced) is installed."""
    nm = ROOT / "node_modules"
    assert nm.is_dir(), "node_modules missing — run `npm install`"
    assert (nm / "inkjs").is_dir(), "inkjs not installed (regression of #3)"
