/**
 * MIR'S END — Station AI Runtime
 *
 * Browser-side runtime for Argon-87, the ship's AI character.
 * Intercepts [AI-PROMPT] tags from Inform 7 output, sends requests
 * to the local proxy server, and renders responses in the story panel.
 *
 * Architecture:
 *   1. Inform 7 emits [AI-PROMPT: topic=<noun> text=<verbatim>]
 *   2. This module intercepts the tag, builds a request payload
 *   3. POSTs to localhost:8787/v1/call with game state + conversation history
 *   4. Renders the response in #story-output with Argon-87 styling
 *   5. Parses any state-affecting tags ([AI-SET:], [AI-REVEAL:], [AI-NUDGE:])
 */

(() => {
  /* ── Constants ── */

  var PROXY_URL = "http://localhost:8787/v1/call";
  var REQUEST_TIMEOUT_MS = 15000;
  var MAX_CONVERSATION_HISTORY = 10;
  var FALLBACK_MESSAGE =
    "Argon-87's voice stutters. Static fills the channel. He does not respond.";

  /* ── AI-PROMPT tag pattern ──
     Format: [AI-PROMPT: topic=<noun> text=<verbatim player text>]
     The topic and text fields are optional; bare [AI-PROMPT] is valid. */
  var AI_PROMPT_RE =
    /\[AI-PROMPT(?::?\s*(?:topic=([^\]]*?)\s*)?(?:text=([^\]]*?))?)?\]/;

  /* ── State-affecting tag patterns ──
     [AI-SET: key value]
     [AI-REVEAL: key]
     [AI-NUDGE: key] */
  var AI_SET_RE = /\[AI-SET:\s*([a-z0-9_-]+)\s+([^\]]+)\]/gi;
  var AI_REVEAL_RE = /\[AI-REVEAL:\s*([a-z0-9_-]+)\]/gi;
  var AI_NUDGE_RE = /\[AI-NUDGE:\s*([a-z0-9_-]+)\]/gi;

  /* ── Whitelist for state-affecting tags ──
     Empty for MVP; populated as game features require AI state writes.
     Keys must match exactly. Values are not validated beyond presence. */
  var STATE_TAG_WHITELIST = {
    // "player-trusts-argon": true,
    // "hidden-room-known": true,
    // "restore-power": true,
  };

  /* ── Conversation memory (session-scoped) ── */
  var conversationHistory = [];

  /* ── In-flight request guard ── */
  var requestInFlight = false;

  /* ── Public API ── */

  /**
   * Check whether a line of story text contains an AI-PROMPT tag.
   * Returns the parsed tag data or null.
   */
  function matchAiPromptTag(text) {
    var m = text.match(AI_PROMPT_RE);
    if (!m) return null;
    return {
      topic: (m[1] || "").trim(),
      text: (m[2] || "").trim(),
    };
  }

  /**
   * Handle an AI prompt: build the request, call the proxy, render the response.
   * Returns a promise that resolves when the response has been rendered.
   */
  async function handleAiPrompt(promptData) {
    if (requestInFlight) {
      appendArgonText(
        "Argon-87's voice crackles with interference. Wait a moment.",
      );
      return;
    }

    requestInFlight = true;

    try {
      var gameState = buildGameState();
      var playerInput = promptData.text || promptData.topic || "talk";

      var payload = {
        role: "station-ai",
        game_state: gameState,
        player_input: playerInput,
        conversation_history: conversationHistory.slice(
          -MAX_CONVERSATION_HISTORY,
        ),
      };

      var responseText = await callProxy(payload);

      // Parse and apply any state-affecting tags before display
      var stateEffects = parseStateEffectTags(responseText);
      applyStateEffects(stateEffects);

      // Strip state tags from the display text
      var displayText = stripStateTags(responseText);

      if (displayText.trim()) {
        appendArgonText(displayText.trim());
      }

      // Record the exchange in conversation memory
      conversationHistory.push({
        role: "player",
        content: playerInput,
      });
      conversationHistory.push({
        role: "argon",
        content: displayText.trim(),
      });
    } catch (err) {
      console.warn("[StationAI] Proxy call failed:", err.message || err);
      appendArgonText(FALLBACK_MESSAGE);
    } finally {
      requestInFlight = false;
    }
  }

  /**
   * Build a game state snapshot for the proxy request.
   */
  function buildGameState() {
    var mirsEnd = window.MirsEnd;
    if (!mirsEnd) return {};

    var state = mirsEnd.getState();
    return {
      currentRoom: state.currentRoom,
      o2: state.o2,
      morale: state.morale,
      inventory: state.inventory,
      gameStarted: state.gameStarted,
    };
  }

  /**
   * POST to the proxy server and return the response text.
   * Throws on timeout, network error, or non-2xx status.
   */
  async function callProxy(payload) {
    var controller = new AbortController();
    var timeoutId = setTimeout(
      () => controller.abort(),
      REQUEST_TIMEOUT_MS,
    );

    try {
      var response = await fetch(PROXY_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error("Proxy returned HTTP " + response.status);
      }

      var data = await response.json();
      return data.text || data.response || data.content || "";
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Append Argon-87's response to the story panel with distinctive styling.
   */
  function appendArgonText(text) {
    var mirsEnd = window.MirsEnd;
    if (!mirsEnd) return;

    var storyOutput = document.getElementById("story-output");
    if (!storyOutput) return;

    var wrapper = document.createElement("div");
    wrapper.className = "argon-speech";

    var label = document.createElement("span");
    label.className = "argon-label";
    label.textContent = "ARGON-87: ";

    var content = document.createElement("span");
    content.className = "argon-text";
    content.textContent = text;

    wrapper.appendChild(label);
    wrapper.appendChild(content);
    storyOutput.appendChild(wrapper);

    // Scroll to bottom
    var panel = document.getElementById("story-panel");
    if (panel) panel.scrollTop = panel.scrollHeight;
  }

  /* ── State-affecting tag parsing ── */

  /**
   * Parse [AI-SET:], [AI-REVEAL:], and [AI-NUDGE:] tags from the response.
   * Returns an array of { type, key, value } objects.
   */
  function parseStateEffectTags(text) {
    var effects = [];
    var m;

    // Reset regex lastIndex for global patterns
    AI_SET_RE.lastIndex = 0;
    AI_REVEAL_RE.lastIndex = 0;
    AI_NUDGE_RE.lastIndex = 0;

    while ((m = AI_SET_RE.exec(text)) !== null) {
      effects.push({ type: "set", key: m[1], value: m[2].trim() });
    }
    while ((m = AI_REVEAL_RE.exec(text)) !== null) {
      effects.push({ type: "reveal", key: m[1], value: true });
    }
    while ((m = AI_NUDGE_RE.exec(text)) !== null) {
      effects.push({ type: "nudge", key: m[1], value: true });
    }

    return effects;
  }

  /**
   * Apply validated state effects through the existing setState bridge.
   * Only whitelisted keys are allowed; others are logged and ignored.
   */
  function applyStateEffects(effects) {
    for (var i = 0; i < effects.length; i++) {
      var effect = effects[i];
      if (!STATE_TAG_WHITELIST[effect.key]) {
        console.log(
          "[StationAI] Ignoring non-whitelisted state tag:",
          effect.type,
          effect.key,
        );
        continue;
      }
      // Apply through the public MirsEnd API
      var mirsEnd = window.MirsEnd;
      if (mirsEnd && mirsEnd.setState) {
        var update = {};
        update[effect.key] = effect.value;
        mirsEnd.setState(update);
        console.log("[StationAI] Applied state effect:", effect);
      }
    }
  }

  /**
   * Strip state-affecting tags from response text before display.
   */
  function stripStateTags(text) {
    return text
      .replace(/\[AI-SET:\s*[a-z0-9_-]+\s+[^\]]+\]/gi, "")
      .replace(/\[AI-REVEAL:\s*[a-z0-9_-]+\]/gi, "")
      .replace(/\[AI-NUDGE:\s*[a-z0-9_-]+\]/gi, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  /**
   * Reset conversation history. Called on new game.
   */
  function resetConversation() {
    conversationHistory = [];
    requestInFlight = false;
  }

  /**
   * Get current conversation history (for testing/debugging).
   */
  function getConversationHistory() {
    return conversationHistory.slice();
  }

  /* ── Public interface ── */
  window.StationAI = {
    matchAiPromptTag: matchAiPromptTag,
    handleAiPrompt: handleAiPrompt,
    resetConversation: resetConversation,
    getConversationHistory: getConversationHistory,
    appendArgonText: appendArgonText,
    parseStateEffectTags: parseStateEffectTags,
    stripStateTags: stripStateTags,
    /* Exposed for testing */
    _config: {
      PROXY_URL: PROXY_URL,
      REQUEST_TIMEOUT_MS: REQUEST_TIMEOUT_MS,
      MAX_CONVERSATION_HISTORY: MAX_CONVERSATION_HISTORY,
      FALLBACK_MESSAGE: FALLBACK_MESSAGE,
    },
  };
})();
