"""Tests for the local AI proxy server (scripts/ai-proxy.py).

All Claude API calls are mocked; no real API key or network access needed.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure the lib directory is importable.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "lib"))

from mirs_end_bridge.claude import reset_cost_report
from mirs_end_bridge.logs import set_log_dir

# Set API key before importing the proxy module.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-pytest")

# Import ai-proxy.py (hyphenated filename) via importlib.
_proxy_path = _PROJECT_ROOT / "scripts" / "ai-proxy.py"
_spec = importlib.util.spec_from_file_location("ai_proxy", _proxy_path)
ai_proxy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ai_proxy)
sys.modules["ai_proxy"] = ai_proxy  # Register so unittest.mock.patch can find it.

app = ai_proxy.app
ALLOWED_ORIGIN = ai_proxy.ALLOWED_ORIGIN
VALID_ROLES = ai_proxy.VALID_ROLES

# ── Fixtures ─────────────────────────────────────────────────────────────────

GOOD_ORIGIN = ALLOWED_ORIGIN


@pytest.fixture(autouse=True)
def _clean_state(tmp_path):
    """Reset cost report, rate limiter, and redirect logs for each test."""
    reset_cost_report()
    set_log_dir(tmp_path / "logs")
    ai_proxy._rate_store.clear()
    yield
    set_log_dir(None)


@pytest.fixture()
def client():
    """FastAPI test client."""
    return TestClient(app, raise_server_exceptions=False)


def _good_payload(**overrides) -> dict:
    """Return a valid /v1/call request payload."""
    payload = {
        "role": "station-ai",
        "game_state": {
            "currentRoom": "Command Module",
            "inventory": ["multimeter"],
            "truthStates": {"power-is-restored": False},
            "resources": {"o2": 92, "morale": 75, "dose": None},
            "score": 10,
            "turn": 5,
            "recentTranscript": "",
            "shipState": {},
        },
        "player_input": "What happened?",
        "conversation_history": [],
    }
    payload.update(overrides)
    return payload


# ── Health check ─────────────────────────────────────────────────────────────


class TestHealthCheck:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ── Successful request ───────────────────────────────────────────────────────


class TestSuccessfulCall:
    @patch("ai_proxy.call_claude")
    def test_valid_request_returns_response(self, mock_call, client):
        from mirs_end_bridge.types import LLMResponse

        mock_call.return_value = LLMResponse(
            text="The impact damaged forward module.",
            input_tokens=150,
            output_tokens=40,
            cost_usd=0.001,
        )

        resp = client.post(
            "/v1/call",
            json=_good_payload(),
            headers={"Origin": GOOD_ORIGIN},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "The impact damaged forward module."
        assert data["usage"]["input_tokens"] == 150
        assert data["usage"]["output_tokens"] == 40
        assert data["usage"]["cost_usd"] == 0.001

    @patch("ai_proxy.call_claude")
    def test_conversation_history_passed(self, mock_call, client):
        from mirs_end_bridge.types import LLMResponse

        mock_call.return_value = LLMResponse(
            text="Response.",
            input_tokens=100,
            output_tokens=20,
            cost_usd=0.0005,
        )

        payload = _good_payload(
            conversation_history=[
                {"role": "player", "content": "Hello"},
                {"role": "assistant", "content": "Greetings."},
            ]
        )
        resp = client.post(
            "/v1/call",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )

        assert resp.status_code == 200

    @patch("ai_proxy.call_claude")
    def test_all_valid_roles_accepted(self, mock_call, client):
        from mirs_end_bridge.types import LLMResponse

        mock_call.return_value = LLMResponse(
            text="Ok.",
            input_tokens=50,
            output_tokens=10,
            cost_usd=0.0001,
        )

        for role in VALID_ROLES:
            resp = client.post(
                "/v1/call",
                json=_good_payload(role=role),
                headers={"Origin": GOOD_ORIGIN},
            )
            assert resp.status_code == 200, f"Role {role} should be accepted"


# ── Invalid requests (400/422) ───────────────────────────────────────────────


class TestInvalidRequests:
    def test_missing_role_returns_422(self, client):
        payload = _good_payload()
        del payload["role"]
        resp = client.post(
            "/v1/call",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 422

    def test_missing_game_state_returns_422(self, client):
        payload = _good_payload()
        del payload["game_state"]
        resp = client.post(
            "/v1/call",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 422

    def test_missing_player_input_returns_422(self, client):
        payload = _good_payload()
        del payload["player_input"]
        resp = client.post(
            "/v1/call",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 422

    def test_invalid_role_returns_400(self, client):
        resp = client.post(
            "/v1/call",
            json=_good_payload(role="hacker"),
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 400
        assert "Invalid role" in resp.json()["detail"]

    def test_empty_body_returns_422(self, client):
        resp = client.post(
            "/v1/call",
            content=b"{}",
            headers={"Origin": GOOD_ORIGIN, "Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_non_json_body_returns_422(self, client):
        resp = client.post(
            "/v1/call",
            content=b"not json",
            headers={"Origin": GOOD_ORIGIN, "Content-Type": "application/json"},
        )
        assert resp.status_code == 422


# ── Origin check ─────────────────────────────────────────────────────────────


class TestOriginCheck:
    def test_missing_origin_rejected(self, client):
        resp = client.post("/v1/call", json=_good_payload())
        assert resp.status_code == 403
        assert "Origin not allowed" in resp.json()["detail"]

    def test_wrong_origin_rejected(self, client):
        resp = client.post(
            "/v1/call",
            json=_good_payload(),
            headers={"Origin": "http://evil.example.com"},
        )
        assert resp.status_code == 403

    @patch("ai_proxy.call_claude")
    def test_correct_origin_accepted(self, mock_call, client):
        from mirs_end_bridge.types import LLMResponse

        mock_call.return_value = LLMResponse(
            text="Ok.", input_tokens=50, output_tokens=10, cost_usd=0.0001,
        )
        resp = client.post(
            "/v1/call",
            json=_good_payload(),
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 200


# ── Rate limiting ────────────────────────────────────────────────────────────


class TestRateLimiting:
    @patch("ai_proxy.call_claude")
    def test_rate_limit_exceeded(self, mock_call, client):
        from mirs_end_bridge.types import LLMResponse

        mock_call.return_value = LLMResponse(
            text="Ok.", input_tokens=50, output_tokens=10, cost_usd=0.0001,
        )

        original_limit = ai_proxy.RATE_LIMIT_PER_MINUTE
        ai_proxy.RATE_LIMIT_PER_MINUTE = 3

        try:
            for i in range(3):
                resp = client.post(
                    "/v1/call",
                    json=_good_payload(),
                    headers={"Origin": GOOD_ORIGIN},
                )
                assert resp.status_code == 200, f"Request {i+1} should succeed"

            # Fourth request should be rate limited.
            resp = client.post(
                "/v1/call",
                json=_good_payload(),
                headers={"Origin": GOOD_ORIGIN},
            )
            assert resp.status_code == 429
            assert "Rate limit" in resp.json()["detail"]
        finally:
            ai_proxy.RATE_LIMIT_PER_MINUTE = original_limit


# ── API key never leaked ─────────────────────────────────────────────────────


class TestApiKeyNeverLeaked:
    def test_api_key_not_in_error_response(self, client):
        """Error responses must not contain the API key."""
        resp = client.post(
            "/v1/call",
            json=_good_payload(role="invalid"),
            headers={"Origin": GOOD_ORIGIN},
        )
        body = resp.text
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            assert api_key not in body

    @patch("ai_proxy.call_claude")
    def test_api_key_not_in_success_response(self, mock_call, client):
        from mirs_end_bridge.types import LLMResponse

        mock_call.return_value = LLMResponse(
            text="Ok.", input_tokens=50, output_tokens=10, cost_usd=0.0001,
        )
        resp = client.post(
            "/v1/call",
            json=_good_payload(),
            headers={"Origin": GOOD_ORIGIN},
        )
        body = resp.text
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            assert api_key not in body

    @patch("ai_proxy.call_claude", side_effect=Exception("Something broke"))
    def test_api_key_not_in_500_response(self, mock_call, client):
        resp = client.post(
            "/v1/call",
            json=_good_payload(),
            headers={"Origin": GOOD_ORIGIN},
        )
        body = resp.text
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            assert api_key not in body
        assert resp.status_code == 500

    def test_api_key_not_in_logs(self, client, caplog):
        """The API key must never appear in log output."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "test-key-for-pytest")

        with caplog.at_level(logging.DEBUG, logger="ai-proxy"):
            client.post(
                "/v1/call",
                json=_good_payload(),
                headers={"Origin": "http://evil.example.com"},
            )

        for record in caplog.records:
            assert api_key not in record.getMessage()


# ── Missing API key prevents startup ─────────────────────────────────────────


class TestMissingApiKey:
    def test_main_refuses_without_api_key(self):
        """The main() function should exit if ANTHROPIC_API_KEY is unset."""
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                ai_proxy.main()
            assert exc_info.value.code == 1


# ── Bridge API errors ────────────────────────────────────────────────────────


class TestBridgeErrors:
    @patch("ai_proxy.call_claude")
    def test_bridge_api_error_returns_502(self, mock_call, client):
        from mirs_end_bridge.claude import BridgeAPIError

        mock_call.side_effect = BridgeAPIError("API failed", status_code=None)
        resp = client.post(
            "/v1/call",
            json=_good_payload(),
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 502

    @patch("ai_proxy.call_claude")
    def test_bridge_rate_limit_returns_429(self, mock_call, client):
        from mirs_end_bridge.claude import BridgeAPIError

        mock_call.side_effect = BridgeAPIError("Rate limited", status_code=429)
        resp = client.post(
            "/v1/call",
            json=_good_payload(),
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 429


# ── Cost cap placeholder (skip until #67 lands) ─────────────────────────────


class TestCostCap:
    @pytest.mark.skip(reason="Cost cap enforcement (#67) not yet implemented")
    def test_cost_cap_returns_402(self, client):
        """Once #67 lands, exceeding the cost cap should return 402."""
        pass


# ── /v1/sessions ingest ─────────────────────────────────────────────────────


class TestSessionIngest:
    """The /v1/sessions endpoint persists playthroughs to the SQLite DB."""

    @pytest.fixture()
    def session_db(self, tmp_path, monkeypatch):
        db = tmp_path / "playthroughs.sqlite"
        monkeypatch.setenv("MIRSEND_DB_PATH", str(db))
        return db

    def _payload(self, **overrides) -> dict:
        base = {
            "session_id": "abc-123",
            "started_at": "2026-04-28T12:00:00+00:00",
            "ended_at": "2026-04-28T12:30:00+00:00",
            "status": "completed",
            "ending_type": "transmit",
            "final_score": 14,
            "final_o2": 80,
            "final_morale": 72,
            "player_kind": "human",
            "game_version": "develop",
            "command_history": ["look", "open locker"],
            "transcript": "...",
        }
        base.update(overrides)
        return base

    def test_browser_shape_writes_session(self, client, session_db):
        """Browser sends turns as int + final_state dict + command_history."""
        payload = self._payload(
            turns=2,
            final_state={"score": 14, "o2": 80, "morale": 72},
        )
        resp = client.post(
            "/v1/sessions",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["counts"]["sessions"] == 1
        # Two turns reconstructed from command_history.
        assert body["counts"]["turns"] == 2

        from playthrough_db import get_session  # noqa: PLC0415
        row = get_session("abc-123", db_path=session_db)
        assert row is not None
        assert row["status"] == "completed"
        assert row["ending_type"] == "transmit"
        assert row["final_o2"] == 80

    def test_driver_shape_with_flat_finals(self, client, session_db):
        payload = self._payload(
            command_history=["look", "n", "transmit"],
        )
        resp = client.post(
            "/v1/sessions",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 200
        from playthrough_db import get_session  # noqa: PLC0415
        row = get_session("abc-123", db_path=session_db)
        assert row is not None
        assert len(row["turns"]) == 3

    def test_pool_shape_with_full_turn_dicts(self, client, session_db):
        """Pool worker sends full per-turn dicts."""
        payload = self._payload(
            turns=[
                {"turn_number": 1, "command": "look",
                 "response": "You see...", "current_room": "Crew Quarters"},
                {"turn_number": 2, "command": "open locker",
                 "response": "Open.", "current_room": "Crew Quarters"},
            ],
        )
        resp = client.post(
            "/v1/sessions",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 200
        from playthrough_db import get_session  # noqa: PLC0415
        row = get_session("abc-123", db_path=session_db)
        assert row["turns"][0]["response"] == "You see..."
        assert row["turns"][0]["current_room"] == "Crew Quarters"

    def test_idempotent_on_session_id(self, client, session_db):
        """Re-POSTing the same session_id replaces, doesn't duplicate."""
        client.post(
            "/v1/sessions",
            json=self._payload(turns=2),
            headers={"Origin": GOOD_ORIGIN},
        )
        resp = client.post(
            "/v1/sessions",
            json=self._payload(turns=5, command_history=["a", "b", "c", "d", "e"]),
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 200

        from playthrough_db import list_sessions  # noqa: PLC0415
        sessions = list_sessions(db_path=session_db)
        assert len(sessions) == 1  # still one session row, not two
        assert sessions[0]["id"] == "abc-123"

    def test_missing_session_id_returns_400(self, client, session_db):
        resp = client.post(
            "/v1/sessions",
            json={"started_at": "2026-04-28T12:00:00+00:00"},
            headers={"Origin": GOOD_ORIGIN},
        )
        assert resp.status_code == 400
        assert "session_id" in resp.json()["detail"]

    def test_metadata_is_persisted(self, client, session_db):
        payload = self._payload(
            metadata={"bailout_reason": "ending", "estimated_cost_usd": "0.42"},
        )
        client.post(
            "/v1/sessions",
            json=payload,
            headers={"Origin": GOOD_ORIGIN},
        )
        from playthrough_db import get_session  # noqa: PLC0415
        row = get_session("abc-123", db_path=session_db)
        assert row["metadata"]["bailout_reason"] == "ending"
        assert row["metadata"]["estimated_cost_usd"] == "0.42"
