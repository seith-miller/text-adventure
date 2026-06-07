"""Tests for mirs_end_bridge.voice_kit."""

import pytest

from mirs_end_bridge.voice_kit import clear_cache, get_voice_kit


@pytest.fixture(autouse=True)
def _clear_voice_cache():
    """Ensure cache is clean before each test."""
    clear_cache()
    yield
    clear_cache()


class TestGetVoiceKit:
    def test_narrator_has_core_files(self):
        kit = get_voice_kit("narrator")
        assert "darkling_beetles" in kit
        assert "the_man_ava" in kit
        assert "writing_style" in kit

    def test_narrator_no_persona(self):
        kit = get_voice_kit("narrator")
        assert "station_ai_persona" not in kit

    def test_station_ai_includes_persona(self):
        kit = get_voice_kit("station-ai")
        assert "station_ai_persona" in kit
        assert "Argon-87" in kit["station_ai_persona"]

    def test_content_is_nonempty(self):
        kit = get_voice_kit("narrator")
        for key, value in kit.items():
            assert len(value) > 0, f"Voice file {key} is empty"

    def test_darkling_beetles_content(self):
        kit = get_voice_kit("narrator")
        # The writing sample should reference the darkling beetles
        assert "beetle" in kit["darkling_beetles"].lower()

    def test_writing_style_content(self):
        kit = get_voice_kit("narrator")
        assert "em-dash" in kit["writing_style"].lower()

    def test_cache_returns_same_object(self):
        kit1 = get_voice_kit("narrator")
        kit2 = get_voice_kit("narrator")
        assert kit1 is kit2

    def test_different_roles_cached_separately(self):
        kit_narrator = get_voice_kit("narrator")
        kit_ai = get_voice_kit("station-ai")
        assert kit_narrator is not kit_ai
        assert "station_ai_persona" not in kit_narrator
        assert "station_ai_persona" in kit_ai
