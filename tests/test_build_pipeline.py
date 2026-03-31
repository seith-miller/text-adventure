"""Tests for the Ink compilation pipeline and project setup."""

import json
import os
import subprocess

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


def test_build_story_compiles_ink_to_json():
    result = subprocess.run(
        ["npm", "run", "build:story"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0

    json_path = os.path.join(ROOT, "game", "dist", "story", "main.json")
    assert os.path.isfile(json_path), "Compiled JSON not found"

    with open(json_path) as f:
        data = json.load(f)
    assert "inkVersion" in data, "JSON should be a valid ink story"


def test_build_ts_compiles():
    result = subprocess.run(
        ["npm", "run", "build:ts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0


def test_full_build():
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0


def test_compiled_json_loadable_by_inkjs():
    """Verify the compiled JSON can be loaded by inkjs at runtime."""
    json_path = os.path.join(ROOT, "game", "dist", "story", "main.json")
    if not os.path.isfile(json_path):
        # Build first
        subprocess.run(["npm", "run", "build:story"], cwd=ROOT, timeout=60)

    result = subprocess.run(
        [
            "node",
            "-e",
            (
                "const {Story} = require('inkjs');"
                f"const json = require('fs').readFileSync('{json_path}','utf-8');"
                "const s = new Story(json);"
                "const text = s.ContinueMaximally();"
                "if (!text.includes('awaken')) process.exit(1);"
                "console.log('OK');"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


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
