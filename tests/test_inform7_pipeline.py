"""Tests for the Inform 7 project structure and compilation pipeline."""

import os
import stat
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_inform7_source_exists():
    """Inform 7 source file exists at the expected location."""
    path = os.path.join(ROOT, "game", "inform", "Source", "story.ni")
    assert os.path.isfile(path), "Inform 7 source file not found"


def test_inform7_source_has_title():
    """Source file declares the game title MIR'S END."""
    path = os.path.join(ROOT, "game", "inform", "Source", "story.ni")
    with open(path) as f:
        content = f.read()
    assert '"MIR\'S END"' in content, "Game title not found in source"


def test_inform7_source_has_rooms():
    """Source file defines at least two rooms."""
    path = os.path.join(ROOT, "game", "inform", "Source", "story.ni")
    with open(path) as f:
        content = f.read()
    assert "is a room" in content.lower() or "is a room" in content, (
        "No room definitions found"
    )
    # Check for specific rooms from the story
    assert "Crew Quarters" in content, "Crew Quarters room not found"
    assert "Main Corridor" in content, "Main Corridor room not found"
    assert "Command Module" in content, "Command Module room not found"
    assert "Observation Cupola" in content, "Observation Cupola room not found"


def test_inform7_source_has_objects():
    """Source file defines interactive objects."""
    path = os.path.join(ROOT, "game", "inform", "Source", "story.ni")
    with open(path) as f:
        content = f.read()
    assert "is a thing" in content or "is a container" in content, (
        "No object definitions found"
    )
    # Check for specific objects
    assert "flashlight" in content.lower(), "Flashlight not found"
    assert "radio" in content.lower(), "Radio not found"


def test_inform7_source_has_parser_interaction():
    """Source file includes parser-interactive elements (actions, rules)."""
    path = os.path.join(ROOT, "game", "inform", "Source", "story.ni")
    with open(path) as f:
        content = f.read()
    has_instead = "Instead of" in content
    has_when = "When play begins" in content
    has_action = "switching on" in content.lower() or "examining" in content.lower()
    assert has_instead or has_when or has_action, (
        "No parser interaction rules found"
    )


def test_build_script_exists():
    """The Inform 7 build script exists and is executable."""
    path = os.path.join(ROOT, "scripts", "compile-inform7.sh")
    assert os.path.isfile(path), "Build script not found"
    mode = os.stat(path).st_mode
    assert mode & stat.S_IXUSR, "Build script is not executable"


def test_build_script_checks_source():
    """Build script validates that source file exists."""
    path = os.path.join(ROOT, "scripts", "compile-inform7.sh")
    with open(path) as f:
        content = f.read()
    assert "story.ni" in content, "Build script doesn't reference source file"
    assert "game/dist" in content or "OUTPUT_DIR" in content, (
        "Build script doesn't reference output directory"
    )


def test_build_script_uses_inbuild():
    """Build script orchestrates compilation through inbuild.

    The script was rewritten in d61de4a to use the native Inform 7 toolchain
    (inbuild → inform7 → Inform 6 → Glulx). The earlier Docker fallback
    was removed; this test documents the current contract.
    """
    path = os.path.join(ROOT, "scripts", "compile-inform7.sh")
    with open(path) as f:
        content = f.read()
    assert "inbuild" in content, "Build script no longer drives inbuild"
    assert "INFORM7_HOME" in content or "INFORM7_COMPILER" in content, (
        "Build script does not look up the toolchain via env vars"
    )


def test_package_json_has_build_story():
    """package.json build:story script invokes the Inform 7 compiler."""
    import json

    path = os.path.join(ROOT, "package.json")
    with open(path) as f:
        pkg = json.load(f)
    assert "build:story" in pkg["scripts"], "build:story script not found"
    assert "inform7" in pkg["scripts"]["build:story"] or "compile-inform7" in pkg["scripts"]["build:story"], (
        "build:story does not reference Inform 7 compilation"
    )


def test_build_output_directory_is_gitignored():
    """game/dist/ and Inform 7 build artifacts are git-ignored."""
    path = os.path.join(ROOT, ".gitignore")
    with open(path) as f:
        content = f.read()
    assert "game/dist/" in content, "game/dist/ not in .gitignore"
    assert "game/inform/Build/" in content, "Inform 7 Build dir not in .gitignore"


def test_play_html_exists():
    """Browser play page exists for Quixe/Parchment integration."""
    path = os.path.join(ROOT, "game", "play.html")
    assert os.path.isfile(path), "play.html not found"
    with open(path) as f:
        content = f.read()
    assert "story.ulx" in content, "play.html doesn't reference the story file"
    assert "MIR" in content, "play.html doesn't reference the game title"


def test_readme_has_inform7_instructions():
    """README documents Inform 7 setup and build workflow."""
    path = os.path.join(ROOT, "README.md")
    with open(path) as f:
        content = f.read()
    assert "Inform 7" in content or "inform7" in content, (
        "README doesn't mention Inform 7"
    )
    assert "npm run build:story" in content, (
        "README doesn't document build:story command"
    )
    assert "ulx" in content.lower() or "Glulx" in content, (
        "README doesn't mention Glulx output format"
    )
    assert "ganelson/inform" in content or "inform7.com" in content, (
        "README doesn't link to Inform 7 compiler"
    )


def test_readme_documents_browser_playback():
    """README explains how to play in a browser."""
    path = os.path.join(ROOT, "README.md")
    with open(path) as f:
        content = f.read()
    assert "Quixe" in content or "Parchment" in content, (
        "README doesn't mention browser interpreters"
    )


def test_ink_files_preserved():
    """Original Ink files are kept as reference."""
    opening = os.path.join(ROOT, "game", "story", "opening.ink")
    main = os.path.join(ROOT, "game", "story", "main.ink")
    assert os.path.isfile(opening), "opening.ink removed (should be kept as reference)"
    assert os.path.isfile(main), "main.ink removed (should be kept as reference)"


def test_inform7_project_structure():
    """Inform 7 project has the correct directory structure."""
    source_dir = os.path.join(ROOT, "game", "inform", "Source")
    assert os.path.isdir(source_dir), "Source directory missing"
    story_file = os.path.join(source_dir, "story.ni")
    assert os.path.isfile(story_file), "story.ni missing from Source/"
