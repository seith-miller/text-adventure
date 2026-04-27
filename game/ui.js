/**
 * MIR'S END — Web UI Shell
 * Hitchhiker's Guide-style layout with interpreter I/O interception.
 */

(() => {
  /* ── Room-to-asset mapping ── */
  var ROOM_ART = {
    "crew quarters": "assets/ascii/bunks.txt",
    "main corridor": "assets/ascii/corridor.txt",
    "command module": "assets/ascii/command_module.txt",
    "observation cupola": "assets/ascii/earth_from_orbit.txt",
    darkness: "assets/ascii/darkness.txt",
  };

  /* ── Known room names for location detection ── */
  var KNOWN_ROOMS = [
    "Crew Quarters",
    "Main Corridor",
    "Command Module",
    "Observation Cupola",
  ];

  /* ── Warm AI feature flag ── */
  var AI_ENABLED = (function readAiFlag() {
    /* Check the global variable set in play.html (mirrors the
       MIRSEND_AI_ENABLED env-var / config entry). */
    var raw =
      typeof window.MIRSEND_AI_ENABLED !== "undefined"
        ? window.MIRSEND_AI_ENABLED
        : 0;
    return raw === 1 || raw === "1" || raw === true || raw === "true";
  })();

  var AI_PROXY_URL = "http://localhost:8787";
  var AI_ONBOARDING_KEY = "mirsend_ai_onboarding_seen";
  var AI_CANNED_LINE = "The AI channel is dead. Argon-87's console is dark.";

  /* ── State ── */
  var state = {
    commandHistory: [],
    historyIndex: -1,
    currentRoom: null,
    o2: 100,
    morale: 70,
    inventory: [],
    interpreterReady: false,
    gameStarted: false,
  };

  /* ── Save key for localStorage (inline quick-save fallback) ── */
  var SAVE_KEY = "mirsend_save";

  /* ── Save/Load UI state ── */
  var _saveLoadModalOpen = false;

  /* ── DOM references ── */
  var storyOutput;
  var sceneArt;
  var commandInput;
  var statusO2;
  var statusMorale;
  var barO2Fill;
  var barMoraleFill;
  var inventoryList;
  var titleScreen;
  var menuContinueBtn;
  var ingameMenuBtn;

  /* ── ASCII art cache ── */
  var artCache = {};

  /* ── Initialization ── */
  function init() {
    storyOutput = document.getElementById("story-output");
    sceneArt = document.getElementById("scene-art");
    commandInput = document.getElementById("command-input");
    statusO2 = document.getElementById("status-o2");
    statusMorale = document.getElementById("status-morale");
    barO2Fill = document.querySelector("#status-bar-o2 .bar-fill");
    barMoraleFill = document.querySelector("#status-bar-morale .bar-fill");
    inventoryList = document.getElementById("inventory-list");
    titleScreen = document.getElementById("title-screen");
    menuContinueBtn = document.getElementById("menu-continue");
    ingameMenuBtn = document.getElementById("ingame-menu-btn");

    commandInput.addEventListener("keydown", handleKeyDown);

    /* Menu button handlers */
    document
      .getElementById("menu-new-game")
      .addEventListener("click", startNewGame);
    menuContinueBtn.addEventListener("click", continueGame);
    ingameMenuBtn.addEventListener("click", showMenu);

    /* ESC key to toggle menu during gameplay */
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (window.MirsEndIntro?.isActive()) return;
        if (
          state.gameStarted &&
          titleScreen &&
          !titleScreen.classList.contains("hidden")
        ) {
          hideMenu();
        } else if (state.gameStarted) {
          showMenu();
        }
      }
    });

    /* Focus input on click anywhere (only when game is active, not during intro) */
    document.addEventListener("click", (e) => {
      if (window.MirsEndIntro?.isActive()) return;
      if (
        state.gameStarted &&
        titleScreen.classList.contains("hidden") &&
        !e.target.closest("#title-screen") &&
        !e.target.closest(".menu-btn") &&
        !e.target.closest("#ingame-menu-btn")
      ) {
        commandInput.focus();
      }
    });

    updateStatus();

    /* Wire up save/load UI buttons (SaveManager multi-slot system) */
    initSaveLoadButtons();

    /* Record the playtest session on every change to #story-output. */
    initSessionRecorder();

    /* Check for saved game to enable Continue button */
    checkSavedGame();

    /* Warm AI: badge + first-run onboarding */
    initAiBadge();
    if (AI_ENABLED) {
      showAiOnboardingModal();
    }

    /* Show title screen on launch */
    showMenu();
  }

  /* ── Menu system ── */

  function showMenu() {
    if (titleScreen) {
      titleScreen.classList.remove("hidden");
      checkSavedGame();
    }
  }

  function hideMenu() {
    if (titleScreen) {
      titleScreen.classList.add("hidden");
      if (state.gameStarted) {
        commandInput.focus();
      }
    }
  }

  function checkSavedGame() {
    if (!menuContinueBtn) return;
    var hasSave = false;
    try {
      hasSave =
        typeof localStorage !== "undefined" &&
        localStorage.getItem(SAVE_KEY) !== null;
    } catch (_e) {
      /* localStorage may be unavailable */
    }
    menuContinueBtn.disabled = !hasSave;
  }

  function startNewGame() {
    /* Reset game state */
    state.commandHistory = [];
    state.historyIndex = -1;
    state.currentRoom = null;
    state.o2 = 100;
    state.morale = 70;
    state.inventory = [];
    state.gameStarted = true;
    state.sessionStartedAt = new Date().toISOString();

    /* Reset playthrough-db session tracking (m11). */
    sessionId = generateUUID();
    _gameEndPosted = false;

    /* Clear story output */
    storyOutput.innerHTML = "";

    hideMenu();
    updateStatus();
    loadSceneArt("darkness");

    if (window.StationAI) window.StationAI.resetConversation();

    /* Play intro sequence if available, then hook the interpreter */
    if (window.MirsEndIntro) {
      window.MirsEndIntro.run(() => {
        hookInterpreter();
        commandInput.focus();
      });
    } else {
      hookInterpreter();
      commandInput.focus();
    }
  }

  function continueGame() {
    /* Prefer SaveManager's multi-slot store when available, fall back to
       the inline single-slot SAVE_KEY that gates the menu Continue button. */
    if (window.SaveManager) {
      const recent = window.SaveManager.getMostRecentSave();
      if (recent) {
        window.SaveManager.applyState(recent.data);
        /* applyState covers o2/morale/inventory/currentRoom but not history;
           restore those here so the UI matches the inline-SAVE_KEY path. */
        if (recent.data.commandHistory !== undefined) {
          state.commandHistory = recent.data.commandHistory;
          state.historyIndex = state.commandHistory.length;
        }
        state.gameStarted = true;
        state.sessionStartedAt =
          state.sessionStartedAt || new Date().toISOString();
        storyOutput.innerHTML = "";
        hideMenu();
        updateStatus();
        loadSceneArt(
          state.currentRoom ? state.currentRoom.toLowerCase() : "darkness",
        );
        appendSystemText("[Resumed from last save.]");
        hookInterpreter();
        commandInput.focus();
        return;
      }
    }

    var saved;
    var raw;
    try {
      raw = localStorage.getItem(SAVE_KEY);
      if (!raw) return;
      saved = JSON.parse(raw);
    } catch (_e) {
      return;
    }

    /* Restore saved state */
    if (saved.o2 !== undefined) state.o2 = saved.o2;
    if (saved.morale !== undefined) state.morale = saved.morale;
    if (saved.inventory !== undefined) state.inventory = saved.inventory;
    if (saved.currentRoom !== undefined) state.currentRoom = saved.currentRoom;
    if (saved.commandHistory !== undefined)
      state.commandHistory = saved.commandHistory;
    state.historyIndex = state.commandHistory.length;
    state.gameStarted = true;
    state.sessionStartedAt = state.sessionStartedAt || new Date().toISOString();

    /* Clear story output and show restored message */
    storyOutput.innerHTML = "";

    hideMenu();
    updateStatus();

    loadSceneArt(
      state.currentRoom ? state.currentRoom.toLowerCase() : "darkness",
    );

    appendSystemText("[Game restored.]");
    hookInterpreter();

    commandInput.focus();
  }

  function saveGame() {
    var data;
    try {
      data = {
        version: 1,
        timestamp: new Date().toISOString(),
        o2: state.o2,
        morale: state.morale,
        inventory: state.inventory,
        currentRoom: state.currentRoom,
        commandHistory: state.commandHistory,
      };
      localStorage.setItem(SAVE_KEY, JSON.stringify(data));
      /* Mirror to SaveManager's autosave slot so continueGame (which
         prefers SaveManager) sees the latest data. */
      if (window.SaveManager?.autoSave) {
        window.SaveManager.autoSave();
      }
    } catch (_e) {
      /* localStorage may be unavailable */
    }
  }

  /* ── Argon-87 AI command detection ── */
  var ARGON_CMD_RE =
    /^(talk\s+to|speak\s+to|speak\s+with|ask)\s+argon(-?\s*87)?$/i;

  function isArgonCommand(cmd) {
    return ARGON_CMD_RE.test(cmd.trim());
  }

  /**
   * Check whether the AI proxy is reachable. Returns a promise that
   * resolves to true/false. Never rejects — network errors yield false.
   */
  function checkProxy() {
    return fetch(AI_PROXY_URL, { method: "HEAD", mode: "no-cors" })
      .then(() => true)
      .catch(() => false);
  }

  /**
   * Handle a TALK TO ARGON command when AI is enabled.
   * Checks proxy reachability and falls back to the canned line on failure.
   */
  function handleArgonCommand() {
    checkProxy().then((reachable) => {
      if (!reachable) {
        console.warn(
          "[MirsEnd] AI proxy unreachable — falling back to canned line.",
        );
        appendStoryText(AI_CANNED_LINE);
        return;
      }
      /* Proxy is reachable — the actual runtime (#62) will handle the
         conversation. For now, surface a placeholder until the runtime
         is integrated. */
      appendStoryText("Argon-87's console flickers. A cursor blinks, waiting.");
    });
  }

  /* ── First-run AI onboarding modal ── */
  function showAiOnboardingModal() {
    var seen = false;
    try {
      seen = localStorage.getItem(AI_ONBOARDING_KEY) === "1";
    } catch (_e) {
      /* localStorage unavailable */
    }
    if (seen) return;

    var overlay = document.createElement("div");
    overlay.id = "ai-onboarding-overlay";

    var modal = document.createElement("div");
    modal.id = "ai-onboarding-modal";

    modal.innerHTML =
      "<h2>Argon-87 AI Features</h2>" +
      "<p>This session has <strong>warm AI</strong> enabled. " +
      "You can speak with <strong>Argon-87</strong>, the station's dormant AI, " +
      "using commands like <code>TALK TO ARGON</code>.</p>" +
      "<p>AI responses are generated via a local proxy server and may incur " +
      "API usage costs. You can disable this feature at any time by setting " +
      "<code>MIRSEND_AI_ENABLED=0</code> in the game configuration.</p>" +
      "<p>The core story is fully playable without AI features.</p>" +
      '<button id="ai-onboarding-dismiss">Understood</button>';

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    document
      .getElementById("ai-onboarding-dismiss")
      .addEventListener("click", () => {
        overlay.remove();
        try {
          localStorage.setItem(AI_ONBOARDING_KEY, "1");
        } catch (_e) {
          /* ignore */
        }
      });
  }

  /* ── AI online badge ── */
  function initAiBadge() {
    if (!AI_ENABLED) return;
    var panel = document.getElementById("status-panel");
    if (!panel) return;
    var badge = document.createElement("div");
    badge.id = "ai-status-badge";
    badge.textContent = "AI online";
    panel.appendChild(badge);
  }

  /* ── Command history & input handling ── */
  function handleKeyDown(e) {
    if (e.key === "Enter") {
      const cmd = commandInput.value.trim();
      if (cmd.length === 0) return;

      state.commandHistory.push(cmd);
      state.historyIndex = state.commandHistory.length;
      commandInput.value = "";

      appendPlayerInput(cmd);

      /* Gate Argon-87 commands on the AI feature flag. */
      if (isArgonCommand(cmd)) {
        if (AI_ENABLED) {
          handleArgonCommand();
        } else {
          appendStoryText(AI_CANNED_LINE);
        }
      } else {
        sendToInterpreter(cmd);
      }
      /* Session persistence is handled by a MutationObserver on
         #story-output — it fires for any input path, including the
         Playwright helpers that drive GlkOte's input directly. */
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (state.historyIndex > 0) {
        state.historyIndex--;
        commandInput.value = state.commandHistory[state.historyIndex];
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (state.historyIndex < state.commandHistory.length - 1) {
        state.historyIndex++;
        commandInput.value = state.commandHistory[state.historyIndex];
      } else {
        state.historyIndex = state.commandHistory.length;
        commandInput.value = "";
      }
    }
  }

  /* ── Display functions ── */
  /**
   * Match the machine-readable status line emitted by the Inform 7 every-turn
   * rule. Format: [MIRSEND o2=N morale=N inv=a,b,c]  (inv may be empty)
   */
  var MIRSEND_STATUS_RE = /\[MIRSEND o2=(-?\d+) morale=(-?\d+) inv=([^\]]*)\]/;

  function interceptAiPrompt(text) {
    if (!window.StationAI) return false;
    var match = window.StationAI.matchAiPromptTag(text);
    if (!match) return false;
    window.StationAI.handleAiPrompt(match);
    return true;
  }

  function parseAndApplyMirsendStatus(text) {
    var m = text.match(MIRSEND_STATUS_RE);
    if (!m) return false;
    var o2 = parseInt(m[1], 10);
    var morale = parseInt(m[2], 10);
    var invStr = (m[3] || "").trim();
    var inventory = invStr === "" ? [] : invStr.split(",").map((s) => s.trim());
    state.o2 = o2;
    state.morale = morale;
    state.inventory = inventory;
    updateStatus();
    return true;
  }

  function appendStoryText(text) {
    /* Intercept status lines before they reach the DOM. */
    if (parseAndApplyMirsendStatus(text)) return;

    /* Intercept AI-PROMPT tags from Inform 7 and route to Station AI. */
    if (interceptAiPrompt(text)) return;

    var span = document.createElement("span");
    span.className = "story-text";
    span.textContent = `${text}\n\n`;
    storyOutput.appendChild(span);
    scrollToBottom();
    detectRoomChange(text);
    checkForGameEnd(text);
  }

  /* ── Session ingest (m11) ── */

  var SESSION_INGEST_URL = "http://localhost:8787/v1/sessions";
  var sessionId = null;
  var _gameEndPosted = false;

  function generateUUID() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      var r = (Math.random() * 16) | 0;
      var v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function detectPlayerKind() {
    if (typeof window.MIRSEND_PLAYER_KIND === "string") {
      return window.MIRSEND_PLAYER_KIND;
    }
    try {
      const params = new URLSearchParams(window.location.search);
      const player = params.get("player");
      if (player) return player;
    } catch (_e) {
      /* ignore */
    }
    return "human";
  }

  function detectGameVersion() {
    const meta = document.querySelector('meta[name="game-version"]');
    return meta ? meta.getAttribute("content") || "unknown" : "unknown";
  }

  function buildSessionPayload() {
    const session = snapshotSession();
    return {
      session_id: sessionId,
      player_kind: detectPlayerKind(),
      game_version: detectGameVersion(),
      started_at: session.startedAt,
      ended_at: session.exportedAt,
      status: _gameEndPosted ? "completed" : "in_progress",
      turns: session.turnCount,
      command_history: session.commandHistory,
      transcript: session.transcript,
      final_state: session.finalState,
    };
  }

  function postSession() {
    if (!sessionId) return;
    try {
      const payload = buildSessionPayload();
      fetch(SESSION_INGEST_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then((res) => {
          if (res.status >= 400 && res.status < 500) {
            console.warn(`[MirsEnd] Session POST returned ${res.status}`);
          } else if (res.status >= 500) {
            console.warn(`[MirsEnd] Session POST server error: ${res.status}`);
          }
        })
        .catch((_err) => {
          /* Proxy unreachable - swallow silently. */
        });
    } catch (_e) {
      /* Swallow any synchronous errors. */
    }
  }

  function checkForGameEnd(text) {
    if (_gameEndPosted) return;
    if (
      typeof text === "string" &&
      (text.indexOf("[Game ended]") !== -1 ||
        text.indexOf("suffocate") !== -1 ||
        text.indexOf("SUFFOCATE") !== -1)
    ) {
      _gameEndPosted = true;
      postSession();
    }
  }

  function appendPlayerInput(text) {
    var span = document.createElement("span");
    span.className = "player-input";
    span.textContent = `> ${text}\n`;
    storyOutput.appendChild(span);
    scrollToBottom();
  }

  function appendSystemText(text) {
    var span = document.createElement("span");
    span.className = "system-text";
    span.textContent = `${text}\n`;
    storyOutput.appendChild(span);
    scrollToBottom();
  }

  function scrollToBottom() {
    var panel = document.getElementById("story-panel");
    panel.scrollTop = panel.scrollHeight;
  }

  /* ── Room detection from story output ── */
  function detectRoomChange(text) {
    for (let i = 0; i < KNOWN_ROOMS.length; i++) {
      const room = KNOWN_ROOMS[i];
      /* Match room name at start of line or as standalone line */
      if (
        text.indexOf(room) !== -1 &&
        (text.indexOf(`${room}\n`) !== -1 ||
          text.substring(0, room.length) === room)
      ) {
        setCurrentRoom(room);
        return;
      }
    }
  }

  function setCurrentRoom(roomName) {
    var changed = state.currentRoom !== roomName;
    state.currentRoom = roomName;
    var key = roomName.toLowerCase();
    loadSceneArt(key);

    /* Auto-save when entering a new area */
    if (changed && window.SaveManager) {
      const result = window.SaveManager.autoSave();
      if (result.success) {
        appendSystemText("[Auto-saved]");
      }
    }
  }

  /* ── Scene art loading ── */
  function loadSceneArt(key) {
    var path = ROOM_ART[key];
    if (!path) return;

    if (artCache[key]) {
      sceneArt.textContent = artCache[key];
      return;
    }

    fetch(path)
      .then((response) => {
        if (!response.ok) {
          sceneArt.textContent = "[No signal]";
          return;
        }
        return response.text();
      })
      .then((text) => {
        if (text) {
          artCache[key] = text;
          sceneArt.textContent = text;
        }
      })
      .catch(() => {
        sceneArt.textContent = "[No signal]";
      });
  }

  /* ── Status panel updates ── */
  function updateStatus() {
    /* O2 */
    statusO2.textContent = `${state.o2}%`;
    statusO2.className = "status-value";
    if (state.o2 > 50) {
      statusO2.classList.add("good");
      barO2Fill.style.background = "var(--status-green)";
    } else if (state.o2 > 25) {
      statusO2.classList.add("warning");
      barO2Fill.style.background = "var(--status-yellow)";
    } else {
      statusO2.classList.add("danger");
      barO2Fill.style.background = "var(--status-red)";
    }
    barO2Fill.style.width = `${state.o2}%`;

    /* Morale */
    statusMorale.textContent = `${state.morale}%`;
    statusMorale.className = "status-value";
    if (state.morale > 50) {
      statusMorale.classList.add("good");
      barMoraleFill.style.background = "var(--status-green)";
    } else if (state.morale > 25) {
      statusMorale.classList.add("warning");
      barMoraleFill.style.background = "var(--status-yellow)";
    } else {
      statusMorale.classList.add("danger");
      barMoraleFill.style.background = "var(--status-red)";
    }
    barMoraleFill.style.width = `${state.morale}%`;

    /* Inventory */
    inventoryList.innerHTML = "";
    if (state.inventory.length === 0) {
      const li = document.createElement("li");
      li.className = "empty-inventory";
      li.textContent = "Nothing carried";
      inventoryList.appendChild(li);
    } else {
      for (let i = 0; i < state.inventory.length; i++) {
        const item = document.createElement("li");
        item.textContent = state.inventory[i];
        inventoryList.appendChild(item);
      }
    }
  }

  /* ── Interpreter I/O bridge ── */

  /**
   * Hook into Quixe/GlkOte to intercept interpreter output.
   * The interpreter writes to GlkOte windows; we intercept
   * the update callback to route text to our custom panels.
   */
  function hookInterpreter() {
    /* Check if GlkOte is loaded (Quixe) */
    if (typeof window.GlkOte !== "undefined") {
      hookGlkOte();
      return;
    }

    /* Check if parchment is loaded */
    if (typeof window.parchment !== "undefined") {
      hookParchment();
      return;
    }

    /* No interpreter loaded — run in standalone shell mode */
    appendSystemText(
      "[MIR'S END — UI Shell loaded. Waiting for interpreter...]",
    );
    appendSystemText(
      "[Load a Glulx interpreter (Quixe or Parchment) to play the story.]",
    );

    /* Poll for interpreter availability */
    var pollCount = 0;
    var pollInterval = setInterval(() => {
      pollCount++;
      if (typeof window.GlkOte !== "undefined") {
        clearInterval(pollInterval);
        hookGlkOte();
      } else if (typeof window.parchment !== "undefined") {
        clearInterval(pollInterval);
        hookParchment();
      } else if (pollCount > 20) {
        clearInterval(pollInterval);
      }
    }, 500);
  }

  function hookGlkOte() {
    state.interpreterReady = true;

    /* Observe the offscreen #windowport where GlkOte renders the story.
       We can't reliably wrap GlkOte.update (Quixe caches an internal
       reference), so mirror DOM changes instead. */
    observeWindowport();

    appendSystemText("[Interpreter connected.]");

    /* Boot the story now that our hook is installed. */
    if (window.MirsEndBoot) {
      window.MirsEndBoot.start();
    }
  }

  function hookParchment() {
    state.interpreterReady = true;
    appendSystemText("[Parchment interpreter connected.]");
  }

  /**
   * Mirror text from the offscreen GlkOte windowport into our visible
   * #story-output panel. We deduplicate by tracking seen line indices so
   * each line is appended exactly once.
   */
  function observeWindowport() {
    var windowport = document.getElementById("windowport");
    if (!windowport) {
      console.warn(
        "[MirsEnd] #windowport not found; Quixe output won't be mirrored.",
      );
      return;
    }
    var seen = new Set();

    var flush = () => {
      /* GlkOte creates buffer windows with class .WindowBuffer and within them
         a sequence of .BufferLine divs. Take each line's text, append if new. */
      const lines = windowport.querySelectorAll(".BufferLine");
      for (let i = 0; i < lines.length; i++) {
        const key = `line-${i}`;
        if (seen.has(key)) continue;
        const text = lines[i].textContent || "";
        /* Skip empty paragraph breaks but honor real content. */
        if (text.trim().length > 0) {
          appendStoryText(text);
        }
        seen.add(key);
      }
    };

    var observer = new MutationObserver(() => {
      flush();
    });
    observer.observe(windowport, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    /* Initial flush in case content was already painted. */
    flush();
  }

  // Kept for reference; unused after we switched to DOM observation.
  // biome-ignore lint/correctness/noUnusedVariables: retained for future reuse
  function extractGlkText(content) {
    let text = "";
    for (let i = 0; i < content.length; i++) {
      if (typeof content[i] === "string") {
        text += content[i];
      } else if (content[i]?.text) {
        text += content[i].text;
      }
    }
    return text;
  }

  /**
   * Send player command to the interpreter.
   * If no interpreter is loaded, echo a demo response.
   *
   * GlkOte creates an `<input class="Input LineInput">` inside its
   * current buffer window when a line event is pending. We drive that
   * input directly — set value, dispatch Enter — which is the same path
   * a real keyboard user exercises.
   */
  function sendToInterpreter(cmd) {
    if (state.interpreterReady) {
      const glkInput = document.querySelector("#windowport input.LineInput");
      if (glkInput) {
        /* GlkOte listens for keydown on the LineInput (bound via jQuery).
           Set the value, focus, and fire a complete event sequence with
           both native and jQuery paths to cover either binding style. */
        glkInput.value = cmd;
        glkInput.focus();

        const native = new KeyboardEvent("keydown", {
          key: "Enter",
          code: "Enter",
          keyCode: 13,
          which: 13,
          bubbles: true,
          cancelable: true,
        });
        /* keyCode/which are non-writable on native events unless we force them. */
        Object.defineProperty(native, "keyCode", { value: 13 });
        Object.defineProperty(native, "which", { value: 13 });
        glkInput.dispatchEvent(native);

        if (window.jQuery) {
          const $input = window.jQuery(glkInput);
          const jqEvt = window.jQuery.Event("keydown", {
            keyCode: 13,
            which: 13,
            key: "Enter",
          });
          $input.trigger(jqEvt);
        }

        /* Return focus to the visible #command-input so the player can
           keep typing without clicking. Defer slightly: GlkOte may
           re-focus its own LineInput when it renders the next prompt,
           so we wait one frame plus a small timeout to win the race. */
        setTimeout(() => commandInput.focus(), 0);
        setTimeout(() => commandInput.focus(), 50);
        return;
      }
    }
    /* Standalone shell mode — handle basic commands for demo */
    handleShellCommand(cmd);
  }

  /* ── Shell mode (no interpreter) ── */
  function handleShellCommand(cmd) {
    var lower = cmd.toLowerCase().trim();

    if (lower === "save") {
      quickSave();
      return;
    } else if (lower === "restore" || lower === "load") {
      quickLoad();
      return;
    } else if (lower === "saves") {
      showSaveLoadModal("save");
      return;
    } else if (lower === "loads") {
      showSaveLoadModal("load");
      return;
    } else if (lower === "look" || lower === "l") {
      if (!state.currentRoom || state.currentRoom === "darkness") {
        appendStoryText(
          "You wake to nothing.\n\nNo hum of ventilation. No green glow of status panels. Just the hammering of your own pulse and a darkness so complete you cannot tell if your eyes are open.\n\nSomething has gone terribly wrong.",
        );
      } else {
        appendStoryText(`You look around ${state.currentRoom}.`);
      }
    } else if (lower === "inventory" || lower === "i") {
      if (state.inventory.length === 0) {
        appendStoryText("You are carrying nothing.");
      } else {
        appendStoryText(`You are carrying:\n  ${state.inventory.join("\n  ")}`);
      }
    } else if (lower === "north" || lower === "n") {
      if (
        !state.currentRoom ||
        state.currentRoom.toLowerCase() === "darkness"
      ) {
        setCurrentRoom("Crew Quarters");
        appendStoryText(
          "Crew Quarters\n\nYou float in the cramped sleeping bay of Mir-2. Personal effects drift in zero-g: a photograph, a pen, a sachet of reconstituted borscht. The status panel above your bunk is dead black. The main corridor lies to the north.",
        );
      } else if (state.currentRoom === "Crew Quarters") {
        setCurrentRoom("Main Corridor");
        appendStoryText(
          "Main Corridor\n\nThe main corridor of Mir-2 stretches in both directions, a tunnel of drifting debris and dead screens. The crew quarters lie to the south, the command module is to the north, and the observation cupola is to the east.",
        );
      } else if (state.currentRoom === "Main Corridor") {
        setCurrentRoom("Command Module");
        appendStoryText(
          "Command Module\n\nThe command module is a cramped space packed with control panels, all currently dead. A single console flickers with dim, partial life. The main corridor is to the south.",
        );
      } else {
        appendStoryText("You can't go that way.");
      }
    } else if (lower === "south" || lower === "s") {
      if (state.currentRoom === "Main Corridor") {
        setCurrentRoom("Crew Quarters");
        appendStoryText(
          "Crew Quarters\n\nYou float in the cramped sleeping bay of Mir-2.",
        );
      } else if (state.currentRoom === "Command Module") {
        setCurrentRoom("Main Corridor");
        appendStoryText(
          "Main Corridor\n\nThe main corridor of Mir-2 stretches in both directions.",
        );
      } else {
        appendStoryText("You can't go that way.");
      }
    } else if (lower === "east" || lower === "e") {
      if (state.currentRoom === "Main Corridor") {
        setCurrentRoom("Observation Cupola");
        appendStoryText(
          "Observation Cupola\n\nThe observation cupola is a blister of reinforced glass on the station's nadir side. Through the viewport you can see the Earth below — scarred with blooms of orange and white across the nightside.",
        );
      } else {
        appendStoryText("You can't go that way.");
      }
    } else if (lower === "west" || lower === "w") {
      if (state.currentRoom === "Observation Cupola") {
        setCurrentRoom("Main Corridor");
        appendStoryText(
          "Main Corridor\n\nThe main corridor of Mir-2 stretches in both directions.",
        );
      } else {
        appendStoryText("You can't go that way.");
      }
    } else if (lower === "help") {
      appendStoryText(
        "Available commands: look, inventory, north, south, east, west, save, restore, saves, loads, help\n\n[Shell mode — load a Glulx interpreter for the full game experience.]",
      );
    } else {
      appendStoryText(
        "I didn't understand that command. Type 'help' for available commands.",
      );
    }

    updateStatus();
  }

  /* ── Save/Load UI ── */

  /**
   * Show the save/load modal overlay.
   * @param {string} mode - "save" or "load"
   */
  function showSaveLoadModal(mode) {
    closeSaveLoadModal(); // remove any existing modal
    _saveLoadModalOpen = true;

    var overlay = document.createElement("div");
    overlay.id = "save-load-overlay";
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeSaveLoadModal();
    });

    var modal = document.createElement("div");
    modal.id = "save-load-modal";

    var title = document.createElement("h2");
    title.textContent = mode === "save" ? "Save Game" : "Load Game";
    modal.appendChild(title);

    if (!window.SaveManager?.storageAvailable()) {
      const msg = document.createElement("p");
      msg.className = "save-load-error";
      msg.textContent = `localStorage is not available. Cannot ${mode} games.`;
      modal.appendChild(msg);
    } else {
      const slots = window.SaveManager.listSlots();
      for (let i = 0; i < slots.length; i++) {
        ((slot) => {
          const row = document.createElement("div");
          row.className = "save-slot-row";

          const label = document.createElement("span");
          label.className = "save-slot-label";
          label.textContent =
            slot.slot === "auto" ? "Auto-save" : `Slot ${slot.slot}`;

          const summary = document.createElement("span");
          summary.className = "save-slot-summary";
          summary.textContent = slot.summary;

          row.appendChild(label);
          row.appendChild(summary);

          if (mode === "save" && slot.slot !== "auto") {
            const saveBtn = document.createElement("button");
            saveBtn.className = "save-slot-btn";
            saveBtn.textContent = "Save";
            saveBtn.addEventListener("click", () => {
              const result = window.SaveManager.saveToSlot(slot.slot);
              appendSystemText(`[${result.message}]`);
              closeSaveLoadModal();
            });
            row.appendChild(saveBtn);
          } else if (mode === "load" && slot.hasData) {
            const loadBtn = document.createElement("button");
            loadBtn.className = "save-slot-btn";
            loadBtn.textContent = "Load";
            loadBtn.addEventListener("click", () => {
              let result;
              if (slot.slot === "auto") {
                result = window.SaveManager.loadAutoSave();
              } else {
                result = window.SaveManager.loadFromSlot(slot.slot);
              }
              if (result.success) {
                window.SaveManager.applyState(result.data);
                appendSystemText(`[${result.message}]`);
              } else {
                appendSystemText(`[${result.message}]`);
              }
              closeSaveLoadModal();
            });
            row.appendChild(loadBtn);
          }

          modal.appendChild(row);
        })(slots[i]);
      }
    }

    var closeBtn = document.createElement("button");
    closeBtn.id = "save-load-close";
    closeBtn.textContent = "Close";
    closeBtn.addEventListener("click", closeSaveLoadModal);
    modal.appendChild(closeBtn);

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
  }

  function closeSaveLoadModal() {
    _saveLoadModalOpen = false;
    var existing = document.getElementById("save-load-overlay");
    if (existing) existing.remove();
  }

  /**
   * Quick-save to slot 1 (for command-line SAVE).
   */
  function quickSave() {
    if (!window.SaveManager) {
      appendSystemText("[Save system not available.]");
      return;
    }
    var result = window.SaveManager.saveToSlot(1);
    appendSystemText(`[${result.message}]`);
  }

  /**
   * Quick-load from slot 1 or most recent save (for command-line RESTORE).
   */
  function quickLoad() {
    if (!window.SaveManager) {
      appendSystemText("[Save system not available.]");
      return;
    }
    var recent = window.SaveManager.getMostRecentSave();
    if (recent) {
      window.SaveManager.applyState(recent.data);
      appendSystemText("[Game loaded successfully.]");
    } else {
      appendSystemText("[No save data found.]");
    }
  }

  /* ── Wire up sidebar save/load buttons ── */
  function initSaveLoadButtons() {
    var saveBtn = document.getElementById("btn-save");
    var loadBtn = document.getElementById("btn-load");
    var continueBtn = document.getElementById("btn-continue");
    var exportBtn = document.getElementById("btn-export");

    if (saveBtn) {
      saveBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        showSaveLoadModal("save");
      });
    }
    if (loadBtn) {
      loadBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        showSaveLoadModal("load");
      });
    }
    if (continueBtn) {
      continueBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        continueGame();
      });
    }
    if (exportBtn) {
      exportBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        downloadSession();
      });
    }
    /* Ctrl+E / Cmd+E anywhere on the page exports too. */
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "e") {
        e.preventDefault();
        downloadSession();
      }
    });
  }

  /* ── Playtest session recording ── */

  var SESSION_KEY = "mirsend_session";
  var SESSION_FORMAT_VERSION = 1;
  var sessionPersistTimer = null;

  /* Persist the session to localStorage on every turn so a page crash or
     reload doesn't lose the playtest record. */
  function persistSession() {
    if (!state.gameStarted) return;
    try {
      const session = snapshotSession();
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch (_e) {
      /* localStorage may be unavailable or full — silently ignore. */
    }
  }

  /* Observe the story panel for any update (new command echo, new
     interpreter response) and persist the session. Debounced so a burst
     of paragraphs from one response produces a single write. */
  function initSessionRecorder() {
    if (!storyOutput) return;
    var observer = new MutationObserver(() => {
      if (sessionPersistTimer) clearTimeout(sessionPersistTimer);
      sessionPersistTimer = setTimeout(persistSession, 250);
    });
    observer.observe(storyOutput, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  function snapshotSession() {
    return {
      version: SESSION_FORMAT_VERSION,
      startedAt: state.sessionStartedAt || null,
      exportedAt: new Date().toISOString(),
      turnCount: state.commandHistory.length,
      commandHistory: state.commandHistory.slice(),
      transcript: storyOutput ? storyOutput.textContent || "" : "",
      finalState: {
        currentRoom: state.currentRoom,
        o2: state.o2,
        morale: state.morale,
        inventory: state.inventory.slice(),
        gameStarted: state.gameStarted,
      },
    };
  }

  function exportSession() {
    return snapshotSession();
  }

  function downloadSession() {
    var session = snapshotSession();
    /* Also POST to the playthrough-db ingest endpoint (m11). */
    postSession();
    var json = JSON.stringify(session, null, 2);
    var blob = new Blob([json], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    var stamp = (session.startedAt || new Date().toISOString()).replace(
      /[:.]/g,
      "-",
    );
    a.href = url;
    a.download = `mirsend-session-${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    appendSystemText("[Session exported.]");
  }

  /* ── Public API for interpreter integration ── */
  window.MirsEnd = {
    config: {
      aiEnabled: AI_ENABLED,
    },
    appendStoryText: appendStoryText,
    appendPlayerInput: appendPlayerInput,
    appendSystemText: appendSystemText,
    setCurrentRoom: setCurrentRoom,
    updateStatus: updateStatus,
    getState: () => state,
    setState: (newState) => {
      if (newState.o2 !== undefined) state.o2 = newState.o2;
      if (newState.morale !== undefined) state.morale = newState.morale;
      if (newState.inventory !== undefined)
        state.inventory = newState.inventory;
      if (newState.currentRoom !== undefined)
        setCurrentRoom(newState.currentRoom);
      updateStatus();
    },
    showMenu: showMenu,
    hideMenu: hideMenu,
    saveGame: saveGame,
    startNewGame: startNewGame,
    exportSession: exportSession,
    downloadSession: downloadSession,
    showSaveModal: () => showSaveLoadModal("save"),
    showLoadModal: () => showSaveLoadModal("load"),
    quickSave: quickSave,
    quickLoad: quickLoad,
    continueGame: continueGame,
  };

  /* ── Boot ── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
