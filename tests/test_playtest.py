"""Tests for the sandboxed AI playtest driver.

The driver runs an Anthropic tool-use loop against a tightly scoped tool
catalog. These tests verify:

- The tool catalog passed to the model is exactly the four MCP tools
  (no Read/Bash/Edit/etc.).
- The happy path: model emits tool_use, bridge handles, ending detected.
- Stuck-loop bailout fires after N no-state-change turns.
- Missing API key exits cleanly.
- Cost accounting accumulates input + output tokens correctly.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts import playtest as playtest_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Static catalog assertions
# ---------------------------------------------------------------------------


def test_tool_catalog_has_exactly_four_tools():
    names = [t["name"] for t in playtest_mod.TOOLS_SCHEMA]
    assert names == [
        "mirs_end_start_game",
        "mirs_end_send_command",
        "mirs_end_get_state",
        "mirs_end_export_transcript",
    ]


def test_tool_catalog_excludes_developer_tools():
    forbidden = {"Read", "Bash", "Edit", "Write", "Grep", "WebFetch", "Glob"}
    names = {t["name"] for t in playtest_mod.TOOLS_SCHEMA}
    assert names.isdisjoint(forbidden)


def test_system_prompt_is_one_sentence_and_generic():
    prompt = playtest_mod.SYSTEM_PROMPT
    assert prompt == "Play a text-based adventure game using the available tools."
    # No mention of MIR'S END, Argon, Mir-3, Soviet, etc.
    lowered = prompt.lower()
    for leak in ("mir", "argon", "soviet", "1987", "station"):
        assert leak not in lowered


# ---------------------------------------------------------------------------
# Loop behavior
# ---------------------------------------------------------------------------


class FakeBridge:
    """Drop-in for GameBridge; no Playwright, no event loop."""

    def __init__(self, send_command_responses=None, states=None):
        self._send_responses = list(send_command_responses or [])
        self._states = list(states or [])
        self._state_idx = 0
        self.session_id = "fake-session"
        self.calls = []

    def _next_state(self):
        if self._state_idx < len(self._states):
            s = self._states[self._state_idx]
            self._state_idx += 1
            return s
        return self._states[-1] if self._states else {}

    def start_game(self):
        self.calls.append(("start_game", None))
        return {
            "session_id": self.session_id,
            "opening_text": "You wake to the sound of alarms.",
            "state": self._next_state(),
        }

    def send_command(self, session_id, command):
        self.calls.append(("send_command", command))
        text = self._send_responses.pop(0) if self._send_responses else "Nothing happens."
        return {
            "response_text": text,
            "state": self._next_state(),
            "turn": len(self.calls),
        }

    def get_state(self, session_id):
        self.calls.append(("get_state", None))
        return {"state": self._next_state(), "turn": len(self.calls)}

    def export_transcript(self, session_id):
        return {
            "session_id": session_id,
            "started_at": 0.0,
            "command_history": [c for k, c in self.calls if k == "send_command"],
            "transcript": "fake transcript",
            "final_state": self._next_state(),
        }

    def close(self):
        pass


def _make_block(block_type, **kwargs):
    """Build a duck-typed content block (matches Anthropic SDK shape)."""
    block = MagicMock()
    block.type = block_type
    for key, value in kwargs.items():
        setattr(block, key, value)
    return block


def _tool_use_block(tool_id, name, **input_kwargs):
    return _make_block("tool_use", id=tool_id, name=name, input=input_kwargs)


def _text_block(text):
    return _make_block("text", text=text)


def _make_response(content, input_tokens=10, output_tokens=20):
    resp = MagicMock()
    resp.content = content
    resp.usage = MagicMock(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    )
    return resp


class FakeAnthropic:
    def __init__(self, scripted_responses):
        self._scripted = list(scripted_responses)
        self.captured_calls = []

        class _Messages:
            def __init__(inner_self, parent):
                inner_self._parent = parent

            def create(inner_self, **kwargs):
                inner_self._parent.captured_calls.append(kwargs)
                if not inner_self._parent._scripted:
                    raise RuntimeError("FakeAnthropic ran out of scripted responses")
                return inner_self._parent._scripted.pop(0)

        self.messages = _Messages(self)


def _install_anthropic_stub(monkeypatch, fake_client):
    fake_module = types.SimpleNamespace(Anthropic=lambda api_key: fake_client)
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)


def test_happy_path_loop_terminates_on_ending(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    bridge = FakeBridge(
        send_command_responses=[
            "You see a metal locker.",
            "*** You have transmitted the message. Begin preparations ***",
        ],
        states=[
            {"currentRoom": "Sleeping Bay", "inventory": [], "score": 0, "o2": 100, "morale": 80},
            {"currentRoom": "Sleeping Bay", "inventory": [], "score": 0, "o2": 99, "morale": 80},
            {"currentRoom": "Sleeping Bay", "inventory": ["flashlight"], "score": 5, "o2": 98, "morale": 80},
        ],
    )
    monkeypatch.setattr(playtest_mod, "GameBridge", lambda: bridge)

    scripted = [
        _make_response([_tool_use_block("call-1", "mirs_end_start_game")]),
        _make_response([
            _tool_use_block(
                "call-2",
                "mirs_end_send_command",
                session_id=bridge.session_id,
                command="look",
            )
        ]),
        _make_response([
            _tool_use_block(
                "call-3",
                "mirs_end_send_command",
                session_id=bridge.session_id,
                command="transmit",
            )
        ]),
    ]
    fake = FakeAnthropic(scripted)
    _install_anthropic_stub(monkeypatch, fake)

    summary = playtest_mod.run_playtest(no_ingest=True, max_turns=20, stuck_window=10)

    assert summary["bailout_reason"] == "ending"
    assert summary["ending_type"] == "transmit"
    assert summary["status"] == "completed"
    assert summary["turns_count"] == 3
    assert summary["input_tokens"] == 30
    assert summary["output_tokens"] == 60
    # 30 * 3/1M + 60 * 15/1M = 0.00099, rounded to 4 places.
    assert summary["estimated_cost_usd"] == pytest.approx(0.001, abs=1e-3)
    # Catalog passed to API: exactly the four tools, no others.
    first_call = fake.captured_calls[0]
    assert [t["name"] for t in first_call["tools"]] == [
        "mirs_end_start_game",
        "mirs_end_send_command",
        "mirs_end_get_state",
        "mirs_end_export_transcript",
    ]
    # System is passed as a list of content blocks so we can attach a
    # cache_control marker to enable prompt caching.
    assert first_call["system"][0]["text"] == playtest_mod.SYSTEM_PROMPT
    assert first_call["system"][0]["cache_control"] == {"type": "ephemeral"}
    # Tools list is also marked: cache_control on the last tool extends
    # the cached prefix through the entire static section.
    assert first_call["tools"][-1]["cache_control"] == {"type": "ephemeral"}


def test_stuck_loop_bailout_fires_after_n_turns(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    static_state = {
        "currentRoom": "Sleeping Bay",
        "inventory": [],
        "score": 0,
        "o2": 100,
        "morale": 80,
    }
    # Bridge returns the same state every turn.
    bridge = FakeBridge(
        send_command_responses=["Nothing happens."] * 20,
        states=[static_state] * 20,
    )
    monkeypatch.setattr(playtest_mod, "GameBridge", lambda: bridge)

    scripted = [_make_response([_tool_use_block("c0", "mirs_end_start_game")])]
    for i in range(20):
        scripted.append(
            _make_response([
                _tool_use_block(
                    f"c{i+1}",
                    "mirs_end_send_command",
                    session_id=bridge.session_id,
                    command="wait",
                )
            ])
        )
    _install_anthropic_stub(monkeypatch, FakeAnthropic(scripted))

    summary = playtest_mod.run_playtest(
        no_ingest=True, max_turns=30, stuck_window=5
    )

    assert summary["bailout_reason"] == "stuck-loop"
    assert summary["status"] == "stuck"
    # Should bail out around turn 5 (window=5 with constant state).
    assert summary["turns_count"] <= 7


def test_missing_api_key_exits_cleanly(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as exc:
        playtest_mod.run_playtest(no_ingest=True, max_turns=1)
    assert exc.value.code == 2


def test_no_tool_call_bails_out_after_three_in_a_row(monkeypatch):
    """Three consecutive text-only responses end the run; one is tolerated."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    bridge = FakeBridge(states=[{}])
    monkeypatch.setattr(playtest_mod, "GameBridge", lambda: bridge)

    scripted = [
        _make_response([_text_block("Thinking...")]),
        _make_response([_text_block("Still thinking...")]),
        _make_response([_text_block("Yeah no tool.")]),
    ]
    _install_anthropic_stub(monkeypatch, FakeAnthropic(scripted))

    summary = playtest_mod.run_playtest(no_ingest=True, max_turns=20)
    assert summary["bailout_reason"] == "no-tool-call"
    assert summary["turns_count"] == 3


def test_single_text_only_response_does_not_bail(monkeypatch):
    """A single text-only response is tolerated; the next tool_use proceeds."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    bridge = FakeBridge(
        send_command_responses=["Looking..."],
        states=[
            {"currentRoom": "X", "inventory": [], "score": 0, "o2": 100, "morale": 80},
            {"currentRoom": "X", "inventory": [], "score": 0, "o2": 99, "morale": 80},
        ],
    )
    monkeypatch.setattr(playtest_mod, "GameBridge", lambda: bridge)

    scripted = [
        _make_response([_text_block("Let me think.")]),
        _make_response([_tool_use_block("c1", "mirs_end_start_game")]),
        _make_response([
            _tool_use_block(
                "c2", "mirs_end_send_command",
                session_id=bridge.session_id, command="look",
            )
        ]),
    ]
    _install_anthropic_stub(monkeypatch, FakeAnthropic(scripted))

    summary = playtest_mod.run_playtest(no_ingest=True, max_turns=3)
    # Bailout should be max-turns, not no-tool-call: the single
    # text-only response was tolerated, then tool calls continued.
    assert summary["bailout_reason"] == "max-turns"
    assert summary["turns_count"] == 3


def test_state_signature_changes_with_room():
    sig_a = playtest_mod._state_signature(
        {"currentRoom": "A", "o2": 100, "morale": 80, "inventory": [], "turn": 1}
    )
    sig_b = playtest_mod._state_signature(
        {"currentRoom": "B", "o2": 100, "morale": 80, "inventory": [], "turn": 1}
    )
    assert sig_a != sig_b


def test_state_signature_stable_for_same_state():
    state = {
        "currentRoom": "A",
        "o2": 100,
        "morale": 80,
        "inventory": ["x", "y"],
        "turn": 5,
    }
    assert playtest_mod._state_signature(state) == playtest_mod._state_signature(state)


def test_is_ending_recognizes_transmit_climax():
    assert playtest_mod._is_ending(
        {}, "*** Begin preparations for transmission ***"
    )


def test_is_ending_returns_false_for_normal_text():
    assert not playtest_mod._is_ending(
        {}, "You see a metal locker, magnetically latched."
    )


def test_max_turns_caps_loop(monkeypatch):
    """Even with infinite scripted responses, max_turns must stop the loop."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    # Bridge with diverse state so stuck-loop doesn't fire.
    states = [{"currentRoom": f"Room{i}", "o2": 100 - i, "morale": 80, "inventory": [], "score": i} for i in range(50)]
    bridge = FakeBridge(
        send_command_responses=["Something happens."] * 50,
        states=states,
    )
    monkeypatch.setattr(playtest_mod, "GameBridge", lambda: bridge)

    scripted = [_make_response([_tool_use_block("c0", "mirs_end_start_game")])]
    for i in range(50):
        scripted.append(
            _make_response([
                _tool_use_block(
                    f"c{i+1}",
                    "mirs_end_send_command",
                    session_id=bridge.session_id,
                    command="north",
                )
            ])
        )
    _install_anthropic_stub(monkeypatch, FakeAnthropic(scripted))

    summary = playtest_mod.run_playtest(
        no_ingest=True, max_turns=3, stuck_window=10
    )
    assert summary["bailout_reason"] == "max-turns"
    assert summary["turns_count"] == 3


def test_auto_dump_writes_markdown_transcript(monkeypatch, tmp_path):
    """run_playtest writes a per-session markdown file when dump_dir is given."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    bridge = FakeBridge(
        send_command_responses=["You see a locker."],
        states=[
            {"currentRoom": "Crew Quarters", "inventory": [], "score": 0,
             "o2": 100, "morale": 80},
            {"currentRoom": "Crew Quarters", "inventory": [], "score": 0,
             "o2": 99, "morale": 80},
        ],
    )
    monkeypatch.setattr(playtest_mod, "GameBridge", lambda: bridge)

    scripted = [
        _make_response([_tool_use_block("c1", "mirs_end_start_game")]),
        _make_response([
            _tool_use_block(
                "c2", "mirs_end_send_command",
                session_id=bridge.session_id, command="look",
            )
        ]),
    ]
    _install_anthropic_stub(monkeypatch, FakeAnthropic(scripted))

    dump_dir = tmp_path / "runs"
    summary = playtest_mod.run_playtest(
        no_ingest=True, max_turns=2, dump_dir=dump_dir,
    )

    md_files = list(dump_dir.glob("*.md"))
    assert len(md_files) == 1
    text = md_files[0].read_text()
    assert summary["session_id"] in text
    assert "## Turn 1: `look`" in text
    assert "You see a locker." in text


def test_auto_dump_disabled_when_dump_dir_is_none(monkeypatch, tmp_path):
    """No markdown file is written when dump_dir is None."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    bridge = FakeBridge(states=[{}])
    monkeypatch.setattr(playtest_mod, "GameBridge", lambda: bridge)

    scripted = [_make_response([_tool_use_block("c1", "mirs_end_start_game")])]
    _install_anthropic_stub(monkeypatch, FakeAnthropic(scripted))

    dump_dir = tmp_path / "should_not_exist"
    playtest_mod.run_playtest(
        no_ingest=True, max_turns=1, dump_dir=None,
    )

    assert not dump_dir.exists() or list(dump_dir.glob("*.md")) == []
