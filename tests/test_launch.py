"""Tests for scripts/launch.py."""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LAUNCH_SCRIPT = REPO_ROOT / "scripts" / "launch.py"
FIXTURE_KDBX = REPO_ROOT / "tests" / "fixtures" / "keys.kdbx"
FIXTURE_PASSWORD = "test123"
FIXTURE_ENTRY = "test-api-key"
FIXTURE_KEY_VALUE = "sk-test-fake-key-not-real"


def _load_launch_module():
    """Import scripts/launch.py as a module without invoking main()."""
    spec = importlib.util.spec_from_file_location("launch", str(LAUNCH_SCRIPT))
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load launch module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def launch():
    return _load_launch_module()


@pytest.fixture()
def fixture_kdbx_exists():
    if not FIXTURE_KDBX.is_file():
        pytest.skip(f"fixture missing: {FIXTURE_KDBX}")


def test_extract_api_key_happy_path(launch, fixture_kdbx_exists):
    key = launch.extract_api_key(FIXTURE_KDBX, FIXTURE_ENTRY, FIXTURE_PASSWORD)
    assert key == FIXTURE_KEY_VALUE


def test_extract_api_key_missing_db(launch):
    missing = pathlib.Path("/nonexistent/missing.kdbx")
    with pytest.raises(FileNotFoundError) as excinfo:
        launch.extract_api_key(missing, "anything", "test123")
    assert "not found" in str(excinfo.value)


def test_extract_api_key_wrong_password(launch, fixture_kdbx_exists):
    with pytest.raises(ValueError) as excinfo:
        launch.extract_api_key(FIXTURE_KDBX, FIXTURE_ENTRY, "wrong-password")
    assert "incorrect master password" in str(excinfo.value)


def test_extract_api_key_entry_not_found(launch, fixture_kdbx_exists):
    with pytest.raises(LookupError) as excinfo:
        launch.extract_api_key(FIXTURE_KDBX, "nope-not-here", FIXTURE_PASSWORD)
    msg = str(excinfo.value)
    assert "not found" in msg
    assert "test-api-key" in msg
    assert "another-entry" in msg


def test_load_config_defaults(launch, monkeypatch):
    for var in (
        "MIRSEND_KEEPASS_PATH",
        "MIRSEND_KEEPASS_ENTRY",
        "MIRSEND_PROXY_PORT",
        "MIRSEND_WEB_PORT",
        "MIRSEND_SKIP_BUILD",
        "MIRSEND_AI_ENABLED",
    ):
        monkeypatch.delenv(var, raising=False)
    cfg = launch._load_config()
    assert cfg["keepass_entry"] == "mirs-end-in-game"
    assert cfg["proxy_port"] == 8787
    assert cfg["web_port"] == 8080
    assert cfg["skip_build"] is False
    assert cfg["ai_enabled"] is True


def test_load_config_overrides(launch, monkeypatch):
    monkeypatch.setenv("MIRSEND_KEEPASS_PATH", "/tmp/other.kdbx")
    monkeypatch.setenv("MIRSEND_KEEPASS_ENTRY", "different")
    monkeypatch.setenv("MIRSEND_PROXY_PORT", "9999")
    monkeypatch.setenv("MIRSEND_WEB_PORT", "9000")
    monkeypatch.setenv("MIRSEND_SKIP_BUILD", "1")
    monkeypatch.setenv("MIRSEND_AI_ENABLED", "0")
    cfg = launch._load_config()
    assert str(cfg["keepass_path"]) == "/tmp/other.kdbx"
    assert cfg["keepass_entry"] == "different"
    assert cfg["proxy_port"] == 9999
    assert cfg["web_port"] == 9000
    assert cfg["skip_build"] is True
    assert cfg["ai_enabled"] is False


def test_load_config_ai_disabled_when_zero(launch, monkeypatch):
    monkeypatch.setenv("MIRSEND_AI_ENABLED", "0")
    cfg = launch._load_config()
    assert cfg["ai_enabled"] is False
