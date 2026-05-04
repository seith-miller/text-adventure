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

  const PROXY_URL = "http://localhost:8787/v1/call";
  const REQUEST_TIMEOUT_MS = 15000;
  const MAX_CONVERSATION_HISTORY = 10;
  const FALLBACK_MESSAGE =
    "Argon-87's voice stutters. Static fills the channel. He does not respond.";

  /* ── AI-PROMPT tag pattern ──
     Format: [AI-PROMPT: topic=<noun> text=<verbatim player text>]
     The topic and text fields are optional; bare [AI-PROMPT] is valid. */
  const AI_PROMPT_RE =
    /\[AI-PROMPT(?::?\s*(?:topic=([^\]]*?)\s*)?(?:text=([^\]]*?))?)?\]/;

  /* ── Whitelist for state-affecting tags ──
     Empty for MVP; populated as game features require AI state writes.
     Keys must match exactly. Values are not validated beyond presence. */
  const STATE_TAG_WHITELIST = {
    // "player-trusts-argon": true,
    // "hidden-room-known": true,
    // "restore-power": true,
  };

  /* ── Conversation memory (session-scoped) ── */
  let conversationHistory = [];

  /* ── In-flight request guard ── */
  let requestInFlight = false;

  /* ── Public API ── */

  /**
   * Check whether a line of story text contains an AI-PROMPT tag.
   * Returns the parsed tag data or null.
   */
  function matchAiPromptTag(text) {
    const m = text.match(AI_PROMPT_RE);
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
      const gameState = buildGameState();
      const playerInput = promptData.text || promptData.topic || "talk";

      const payload = {
        role: "station-ai",
        game_state: gameState,
        player_input: playerInput,
        conversation_history: conversationHistory.slice(
          -MAX_CONVERSATION_HISTORY,
        ),
      };

      const responseText = await callProxy(payload);

      const stateEffects = parseStateEffectTags(responseText);
      applyStateEffects(stateEffects);

      const displayText = stripStateTags(responseText);

      if (displayText.trim()) {
        appendArgonText(displayText.trim());
      }

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
    const mirsEnd = window.MirsEnd;
    if (!mirsEnd) return {};

    const state = mirsEnd.getState();
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
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(PROXY_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Proxy returned HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.text || data.response || data.content || "";
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Append Argon-87's response to the story panel with distinctive styling.
   */
  function appendArgonText(text) {
    const mirsEnd = window.MirsEnd;
    if (!mirsEnd) return;

    const storyOutput = document.getElementById("story-output");
    if (!storyOutput) return;

    const wrapper = document.createElement("div");
    wrapper.className = "argon-speech";

    const label = document.createElement("span");
    label.className = "argon-label";
    label.textContent = "ARGON-87: ";

    const content = document.createElement("span");
    content.className = "argon-text";
    content.textContent = text;

    wrapper.appendChild(label);
    wrapper.appendChild(content);
    storyOutput.appendChild(wrapper);

    const panel = document.getElementById("story-panel");
    if (panel) panel.scrollTop = panel.scrollHeight;
  }

  /* ── State-affecting tag parsing ── */

  /**
   * Parse [AI-SET:], [AI-REVEAL:], and [AI-NUDGE:] tags from the response.
   * Returns an array of { type, key, value } objects.
   */
  function parseStateEffectTags(text) {
    const effects = [];

    const setRe = /\[AI-SET:\s*([a-z0-9_-]+)\s+([^\]]+)\]/gi;
    const revealRe = /\[AI-REVEAL:\s*([a-z0-9_-]+)\]/gi;
    const nudgeRe = /\[AI-NUDGE:\s*([a-z0-9_-]+)\]/gi;

    let m = setRe.exec(text);
    while (m !== null) {
      effects.push({ type: "set", key: m[1], value: m[2].trim() });
      m = setRe.exec(text);
    }
    m = revealRe.exec(text);
    while (m !== null) {
      effects.push({ type: "reveal", key: m[1], value: true });
      m = revealRe.exec(text);
    }
    m = nudgeRe.exec(text);
    while (m !== null) {
      effects.push({ type: "nudge", key: m[1], value: true });
      m = nudgeRe.exec(text);
    }

    return effects;
  }

  /**
   * Apply validated state effects through the existing setState bridge.
   * Only whitelisted keys are allowed; others are logged and ignored.
   */
  function applyStateEffects(effects) {
    for (let i = 0; i < effects.length; i++) {
      const effect = effects[i];
      if (!STATE_TAG_WHITELIST[effect.key]) {
        console.log(
          "[StationAI] Ignoring non-whitelisted state tag:",
          effect.type,
          effect.key,
        );
        continue;
      }
      const mirsEnd = window.MirsEnd;
      if (mirsEnd?.setState) {
        const update = {};
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
