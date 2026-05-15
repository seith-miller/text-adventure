"""Tests for scripts/make_version.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "make_version.py"


def _load():
    spec = importlib.util.spec_from_file_location("make_version", str(SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["make_version"] = mod
    spec.loader.exec_module(mod)
    return mod


make_version = _load()


def test_build_version_returns_required_keys():
    info = make_version.build_version()
    for key in (
        "semver",
        "git_sha",
        "git_branch",
        "dirty",
        "ulx_sha256",
        "story_serial",
        "built_at",
        "version_string",
    ):
        assert key in info, f"missing key {key}"


def test_version_string_format_clean():
    info = make_version.build_version()
    if info["dirty"]:
        assert info["version_string"].endswith("-dirty")
        assert info["version_string"] == f"{info['semver']}+{info['git_sha']}-dirty"
    else:
        assert info["version_string"] == f"{info['semver']}+{info['git_sha']}"


def test_semver_falls_back_when_package_json_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(make_version, "PACKAGE_JSON", tmp_path / "missing.json")
    assert make_version._read_semver() == "0.0.0"


def test_semver_reads_from_package_json(monkeypatch, tmp_path):
    pkg = tmp_path / "package.json"
    pkg.write_text('{"version": "9.9.9"}')
    monkeypatch.setattr(make_version, "PACKAGE_JSON", pkg)
    assert make_version._read_semver() == "9.9.9"


def test_main_writes_version_json(monkeypatch, tmp_path):
    target = tmp_path / "version.json"
    monkeypatch.setattr(make_version, "VERSION_JSON", target)
    monkeypatch.setattr(make_version, "ULX_PATH", tmp_path / "no.ulx")

    rc = make_version.main()
    assert rc == 0
    data = json.loads(target.read_text())
    assert "version_string" in data
    assert "semver" in data
    # No ulx file means hash is empty.
    assert data["ulx_sha256"] == ""


def test_ulx_sha256_short_hashes_a_real_file(monkeypatch, tmp_path):
    fake_ulx = tmp_path / "story.ulx"
    fake_ulx.write_bytes(b"hello world")
    monkeypatch.setattr(make_version, "ULX_PATH", fake_ulx)

    h = make_version._ulx_sha256_short()
    assert len(h) == 12
    # sha256("hello world") starts with b94d27b9...
    assert h.startswith("b94d27b9")
