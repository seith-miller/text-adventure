"""
Unit tests for the Station AI runtime (game/station-ai-runtime.js).

These tests verify the JavaScript module's pure functions by running
them through Node.js subprocess calls, similar to test_ship_state.py.
"""

import json
import subprocess
import textwrap

import pytest


def run_js(script: str) -> str:
    """Run a JavaScript snippet in Node and return stdout."""
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Node error:\n{result.stderr}")
    return result.stdout.strip()


def run_js_json(script: str):
    """Run a JavaScript snippet and parse JSON output."""
    out = run_js(script)
    return json.loads(out)


# ── Helpers to load the runtime in Node ──────────────────────────────────────

LOAD_RUNTIME = textwrap.dedent("""\
    // Minimal browser shims for Node
    global.window = global;
    global.document = {
        getElementById: () => null,
        createElement: () => ({ className: '', textContent: '', appendChild: () => {} }),
    };
    global.fetch = async () => { throw new Error('no fetch in test'); };
    global.AbortController = class { constructor() { this.signal = {}; } abort() {} };
    global.setTimeout = (fn, ms) => { fn(); return 0; };
    global.clearTimeout = () => {};

    // Load the runtime (it attaches to window.StationAI)
    require('./game/station-ai-runtime.js');
""")


class TestMatchAiPromptTag:
    """Test the AI-PROMPT tag regex matching."""

    def test_full_format(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.matchAiPromptTag(
                '[AI-PROMPT: topic=systems text=How are the systems?]'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert result is not None
        assert result["topic"] == "systems"
        assert result["text"] == "How are the systems?"

    def test_text_only(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.matchAiPromptTag(
                '[AI-PROMPT: text=Hello Argon]'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert result is not None
        assert result["text"] == "Hello Argon"

    def test_topic_only(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.matchAiPromptTag(
                '[AI-PROMPT: topic=reactor]'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert result is not None
        assert result["topic"] == "reactor"

    def test_bare_tag(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.matchAiPromptTag('[AI-PROMPT]');
            console.log(JSON.stringify(r));
        """
        )
        assert result is not None
        assert result["topic"] == ""
        assert result["text"] == ""

    def test_no_match(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.matchAiPromptTag('Just regular text');
            console.log(JSON.stringify(r));
        """
        )
        assert result == "null"

    def test_mirsend_tag_does_not_match(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.matchAiPromptTag(
                '[MIRSEND o2=95 morale=50 inv=flashlight]'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert result == "null"


class TestParseStateEffectTags:
    """Test parsing of [AI-SET:], [AI-REVEAL:], [AI-NUDGE:] tags."""

    def test_ai_set(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.parseStateEffectTags(
                'Hello [AI-SET: trust-level high] world'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert len(result) == 1
        assert result[0]["type"] == "set"
        assert result[0]["key"] == "trust-level"
        assert result[0]["value"] == "high"

    def test_ai_reveal(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.parseStateEffectTags(
                'Look here [AI-REVEAL: hidden-room]'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert len(result) == 1
        assert result[0]["type"] == "reveal"
        assert result[0]["key"] == "hidden-room"

    def test_ai_nudge(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.parseStateEffectTags(
                'Maybe try [AI-NUDGE: restore-power]'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert len(result) == 1
        assert result[0]["type"] == "nudge"
        assert result[0]["key"] == "restore-power"

    def test_multiple_tags(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.parseStateEffectTags(
                '[AI-SET: a b] text [AI-REVEAL: c] more [AI-NUDGE: d]'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert len(result) == 3
        assert result[0]["type"] == "set"
        assert result[1]["type"] == "reveal"
        assert result[2]["type"] == "nudge"

    def test_no_tags(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.parseStateEffectTags(
                'Just a clean response with no tags'
            );
            console.log(JSON.stringify(r));
        """
        )
        assert len(result) == 0


class TestStripStateTags:
    """Test that state-affecting tags are removed from display text."""

    def test_strip_ai_set(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.stripStateTags(
                'Before [AI-SET: key value] after'
            );
            console.log(r);
        """
        )
        assert "[AI-SET" not in result
        assert "Before" in result
        assert "after" in result

    def test_strip_all_types(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.stripStateTags(
                'A [AI-SET: k v] B [AI-REVEAL: r] C [AI-NUDGE: n] D'
            );
            console.log(r);
        """
        )
        assert "[AI-SET" not in result
        assert "[AI-REVEAL" not in result
        assert "[AI-NUDGE" not in result
        assert "A" in result
        assert "D" in result

    def test_no_tags_unchanged(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.stripStateTags('Clean text here');
            console.log(r);
        """
        )
        assert result == "Clean text here"


class TestConversationMemory:
    """Test conversation history management."""

    def test_initial_history_empty(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            const r = window.StationAI.getConversationHistory();
            console.log(JSON.stringify(r));
        """
        )
        assert result == []

    def test_reset_clears_history(self):
        result = run_js_json(
            LOAD_RUNTIME
            + """
            // Manually push some entries for testing
            const h = window.StationAI.getConversationHistory();
            // getConversationHistory returns a copy, so we need to test reset
            window.StationAI.resetConversation();
            const r = window.StationAI.getConversationHistory();
            console.log(JSON.stringify(r));
        """
        )
        assert result == []


class TestConfig:
    """Test that configuration values are exposed correctly."""

    def test_proxy_url(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            console.log(window.StationAI._config.PROXY_URL);
        """
        )
        assert result == "http://localhost:8787/v1/call"

    def test_timeout(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            console.log(window.StationAI._config.REQUEST_TIMEOUT_MS);
        """
        )
        assert int(result) == 15000

    def test_max_history(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            console.log(window.StationAI._config.MAX_CONVERSATION_HISTORY);
        """
        )
        assert int(result) == 10

    def test_fallback_message(self):
        result = run_js(
            LOAD_RUNTIME
            + """
            console.log(window.StationAI._config.FALLBACK_MESSAGE);
        """
        )
        assert "does not respond" in result
