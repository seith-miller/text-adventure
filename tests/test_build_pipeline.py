"""Tests for the project setup and build pipeline.

The project has migrated from Ink to Inform 7. Ink-specific compilation
tests are skipped; see test_inform7_pipeline.py for the new pipeline tests.
"""

import json
import os
import subprocess
import shutil

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_package_json_exists():
    path = os.path.join(ROOT, "package.json")
    assert os.path.isfile(path)
    with open(path) as f:
        pkg = json.load(f)
    assert pkg["name"] == "text-adventure"
    assert pkg["private"] is True
    assert pkg["engines"]["node"] == ">=18"


def test_tsconfig_exists():
    path = os.path.join(ROOT, "tsconfig.json")
    assert os.path.isfile(path)
    with open(path) as f:
        cfg = json.load(f)
    assert cfg["compilerOptions"]["target"] == "ES2022"
    assert cfg["compilerOptions"]["outDir"] == "game/dist"


def test_gitignore_covers_artifacts():
    path = os.path.join(ROOT, ".gitignore")
    assert os.path.isfile(path)
    with open(path) as f:
        content = f.read()
    assert "node_modules/" in content
    assert "game/dist/" in content


def test_npm_install_succeeds():
    result = subprocess.run(
        ["npm", "install"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0


@pytest.mark.skipif(
    shutil.which("inform7") is None and shutil.which("ni") is None,
    reason="Inform 7 compiler not installed",
)
def test_build_story_compiles():
    """build:story compiles Inform 7 source to a Glulx story file."""
    result = subprocess.run(
        ["npm", "run", "build:story"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0

    ulx_path = os.path.join(ROOT, "game", "dist", "story.ulx")
    assert os.path.isfile(ulx_path), "Compiled .ulx not found"


def test_build_ts_compiles():
    result = subprocess.run(
        ["npm", "run", "build:ts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0


def test_readme_exists():
    path = os.path.join(ROOT, "README.md")
    assert os.path.isfile(path)
    with open(path) as f:
        content = f.read()
    assert "npm install" in content
    assert "npm run build" in content


def test_gitkeep_files_preserved():
    """Ensure .gitkeep files were not removed."""
    for d in ["game/tests", "game/assets", "game/src", "world/story"]:
        gk = os.path.join(ROOT, d, ".gitkeep")
        assert os.path.isfile(gk), f".gitkeep missing in {d}"
