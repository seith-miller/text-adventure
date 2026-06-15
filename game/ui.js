/**
 * MIR'S END — Web UI Shell
 * Soviet terminal visual language (#132).
 *
 * Renders an 80×25 character grid into a single <pre id="display">.
 * Story text fills the left 48-char column; status fills the right 25-char
 * sidebar. Box-drawing characters form all borders.
 *
 * All existing runtime hooks (Argon-87 AI, session recording, save/load,
 * interpreter bridge, title screen state machine) are preserved.
 */

(() => {
  /* ── Grid constants (docs/ui-design.md) ── */
  var TOTAL_W = 80;
  var STORY_W = 48;
  var SIDE_W = 25;
  var HEADER_W = 76; // inside outer borders + 1-char pad each side
  var BODY_ROWS = 19; // story/sidebar row count

  /* ── Room-to-asset mapping ── */
  var ROOM_ART = {
    "crew quarters": "assets/ascii/bunks.txt",
    "main corridor": "assets/ascii/corridor.txt",
    "command module": "assets/ascii/command_module.txt",
    "observation cupola": "assets/ascii/earth_from_orbit.txt",
    darkness: "assets/ascii/darkness.txt",
  };

  /* ── Known room names for location detection ──
     Must match the printed name from story.ni exactly. When a room
     prints its name as a buffer line we update the SYS header and
     emit a bilingual heading. */
  var KNOWN_ROOMS = [
    "Crew Quarters",
    "Main Corridor",
    "Command Module",
    "Observation Cupola",
    "Life Support Module",
    "Hydroponics Lab",
    "Armament Bay",
    "Reactor Module",
    "Progress Ferry",
    "Soyuz Ferry",
    "Soyuz Reentry Capsule",
  ];

  // Cyrillic shadow labels for the room-name heading. Keys must match
  // KNOWN_ROOMS exactly. Missing entries fall back to Latin only.
  var ROOM_CYRILLIC = {
    "Crew Quarters": "ОТСЕК ЭКИПАЖА",
    "Main Corridor": "ГЛАВНЫЙ КОРИДОР",
    "Command Module": "КОМАНДНЫЙ МОДУЛЬ",
    "Observation Cupola": "НАБЛЮДАТЕЛЬНЫЙ КУПОЛ",
    "Life Support Module": "СИСТЕМА ЖИЗНЕОБЕСПЕЧЕНИЯ",
    "Hydroponics Lab": "ГИДРОПОННАЯ ЛАБОРАТОРИЯ",
    "Armament Bay": "ОРУЖЕЙНЫЙ ОТСЕК",
    "Reactor Module": "РЕАКТОРНЫЙ МОДУЛЬ",
    "Progress Ferry": "ГРУЗОВОЙ КОРАБЛЬ ПРОГРЕСС",
    "Soyuz Ferry": "СОЮЗ",
    "Soyuz Reentry Capsule": "СПУСКАЕМЫЙ АППАРАТ СОЮЗ",
  };

  /* ── Warm AI feature flag ── */
  var AI_ENABLED = (function readAiFlag() {
    var raw =
      typeof window.MIRSEND_AI_ENABLED !== "undefined"
        ? window.MIRSEND_AI_ENABLED
        : 0;
    return raw === 1 || raw === "1" || raw === true || raw === "true";
  })();

  var AI_PROXY_URL = "http://localhost:8787";
  var AI_ONBOARDING_KEY = "mirsend_ai_onboarding_seen";
  // Neutral fallback when the AI runtime isn't attached this build. The prior
  // wording ("Argon-87's console is dark") contradicted the in-game monitor
  // description after power restoration, which says "the bus is alive again."
  // Keep this line agnostic about bus state so prose and UI agree.
  var AI_CANNED_LINE =
    "You key the channel for Argon-87. No response. The runtime is not attached this watch.";

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
  var HISTORY_KEY = "mirsend_command_history";

  /* ── Optional typing / decode-in effect (m13 #140) ──
     Off by default. When enabled, appendStoryText() reveals characters
     into the visible buffer at typingConfig.charsPerSec, can be skipped
     by any key (or by calling skipTyping()), and queues subsequent
     messages so prose order is preserved. The hidden #story-output DOM
     is always populated synchronously so session recording, transcript
     export, and existing e2e assertions are unaffected. */
  var TYPING_STORAGE_KEY = "mirsend_typing_settings";
  var TYPING_DEFAULT = { enabled: false, charsPerSec: 60 };
  var typingConfig = {
    enabled: TYPING_DEFAULT.enabled,
    charsPerSec: TYPING_DEFAULT.charsPerSec,
  };
  var _activeTyping = null;
  var _typingQueue = [];

  /* ── Save/Load UI state ── */
  var _saveLoadModalOpen = false;

  /* ── DOM references ── */
  var storyOutput; // hidden #story-output (for session recording + e2e)
  var commandInput;
  var titleScreen;
  var menuContinueBtn;
  var ingameMenuBtn;
  var displayPre; // the visible <pre id="display">

  /* ── ASCII art cache ── */
  var artCache = {};

  /* ── Perception variant bank (m5 #41). Loaded once at boot from
       game/perceptions.json. See docs/perception-buckets.md. ── */
  var perceptionBank = null;

  /* ── Story lines buffer (word-wrapped at STORY_W chars) ── */
  var storyLines = [];
  /* Lines above the bottom we've scrolled back. 0 = pinned to bottom. */
  var _storyScrollOffset = 0;
  var SCROLL_PAGE = 10;

  /* Push a line into the story buffer, advancing the scroll offset when the
     user has scrolled back so their visible window stays anchored on the
     same content as new lines arrive. */
  function pushStoryLine(line) {
    var maxOffset;
    storyLines.push(line);
    if (_storyScrollOffset > 0) {
      maxOffset = Math.max(0, storyLines.length - BODY_ROWS);
      _storyScrollOffset = Math.min(_storyScrollOffset + 1, maxOffset);
    }
  }

  function scrollUp(lines) {
    var maxOffset = Math.max(0, storyLines.length - BODY_ROWS);
    _storyScrollOffset = Math.min(_storyScrollOffset + lines, maxOffset);
    renderDisplay();
  }

  function scrollDown(lines) {
    _storyScrollOffset = Math.max(0, _storyScrollOffset - lines);
    renderDisplay();
  }

  function scrollToTop() {
    _storyScrollOffset = Math.max(0, storyLines.length - BODY_ROWS);
    renderDisplay();
  }

  /* ── Typing-effect config + animation engine ── */

  function loadTypingConfig() {
    var raw;
    var saved;
    try {
      raw = localStorage.getItem(TYPING_STORAGE_KEY);
      if (!raw) return;
      saved = JSON.parse(raw);
      if (saved && typeof saved === "object") {
        if (typeof saved.enabled === "boolean")
          typingConfig.enabled = saved.enabled;
        if (typeof saved.charsPerSec === "number" && saved.charsPerSec > 0) {
          typingConfig.charsPerSec = saved.charsPerSec;
        }
      }
    } catch (_e) {
      /* localStorage unavailable or corrupt — keep defaults */
    }
  }

  function persistTypingConfig() {
    try {
      localStorage.setItem(TYPING_STORAGE_KEY, JSON.stringify(typingConfig));
    } catch (_e) {
      /* ignore */
    }
  }

  function getTypingConfig() {
    return {
      enabled: typingConfig.enabled,
      charsPerSec: typingConfig.charsPerSec,
    };
  }

  function setTypingConfig(patch) {
    if (patch && typeof patch === "object") {
      if (typeof patch.enabled === "boolean")
        typingConfig.enabled = patch.enabled;
      if (typeof patch.charsPerSec === "number" && patch.charsPerSec > 0) {
        typingConfig.charsPerSec = patch.charsPerSec;
      }
      persistTypingConfig();
    }
    return getTypingConfig();
  }

  /* Animate one message (an array of word-wrapped lines) into the visible
     story buffer. The slot index stays valid even if other writes append
     above it in the meantime — storyLines.push() is append-only. */
  function startTypingAnimation(wrappedLines) {
    if (!wrappedLines || wrappedLines.length === 0) {
      pushStoryLine("");
      renderDisplay();
      drainTypingQueue();
      return;
    }
    var lineIdx = 0;
    var charIdx = 0;
    var line = wrappedLines[0];
    var ms = Math.max(4, Math.round(1000 / typingConfig.charsPerSec));
    pushStoryLine("");
    var slotIdx = storyLines.length - 1;

    function tick() {
      if (!_activeTyping) return;
      if (lineIdx >= wrappedLines.length) {
        finish(true);
        return;
      }
      if (charIdx >= line.length) {
        lineIdx++;
        charIdx = 0;
        if (lineIdx >= wrappedLines.length) {
          finish(true);
          return;
        }
        line = wrappedLines[lineIdx];
        pushStoryLine("");
        slotIdx = storyLines.length - 1;
        renderDisplay();
        _activeTyping.timer = setTimeout(tick, ms);
        return;
      }
      charIdx++;
      storyLines[slotIdx] = escHtml(line.substring(0, charIdx));
      renderDisplay();
      _activeTyping.timer = setTimeout(tick, ms);
    }

    function finish(natural) {
      if (!_activeTyping) return;
      if (_activeTyping.timer) {
        clearTimeout(_activeTyping.timer);
      }
      if (!natural) {
        /* Skip: fill the current slot, then push remaining lines whole. */
        storyLines[slotIdx] = escHtml(line);
        lineIdx++;
        for (; lineIdx < wrappedLines.length; lineIdx++) {
          pushStoryLine(escHtml(wrappedLines[lineIdx]));
        }
      }
      pushStoryLine("");
      renderDisplay();
      _activeTyping = null;
      drainTypingQueue();
    }

    _activeTyping = { finish: finish, timer: null };
    _activeTyping.timer = setTimeout(tick, ms);
  }

  function skipTyping() {
    if (_activeTyping?.finish) {
      _activeTyping.finish(false);
    }
  }

  function drainTypingQueue() {
    if (_activeTyping) return;
    if (_typingQueue.length === 0) return;
    var next = _typingQueue.shift();
    startTypingAnimation(next);
  }

  function queueOrAnimate(wrappedLines) {
    if (_activeTyping) {
      _typingQueue.push(wrappedLines);
      return;
    }
    startTypingAnimation(wrappedLines);
  }

  /* ── Current input text (for rendering the input line in the grid) ── */
  var currentInputText = "";

  /* ── Text helper functions (from v3-textmode mockup) ── */
  function visLen(s) {
    return s.replace(/<[^>]+>/g, "").replace(/&[a-zA-Z0-9#]+;/g, "X").length;
  }
  function pad(s, w) {
    var n = w - visLen(s);
    return n > 0 ? s + " ".repeat(n) : s;
  }
  function cells(left, right, w) {
    var fill = w - visLen(left) - visLen(right);
    return left + " ".repeat(Math.max(0, fill)) + right;
  }

  /**
   * Escape HTML special characters for safe insertion into the <pre>.
   * Leaves our custom inline tags (<hd>, <bri>, etc.) intact.
   */
  function escHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /**
   * Word-wrap text to a given width. Returns an array of lines.
   * Respects existing newlines in the input.
   */
  function wordWrap(text, width) {
    var result = [];
    var paragraphs = text.split("\n");
    for (let p = 0; p < paragraphs.length; p++) {
      const para = paragraphs[p];
      if (para.length === 0) {
        result.push("");
        continue;
      }
      const words = para.split(/(\s+)/);
      let line = "";
      for (let i = 0; i < words.length; i++) {
        let word = words[i];
        if (line.length + word.length <= width) {
          line += word;
        } else if (line.length === 0) {
          // Word longer than width — force break
          while (word.length > width) {
            result.push(word.substring(0, width));
            word = word.substring(width);
          }
          line = word;
        } else {
          result.push(line.replace(/\s+$/, ""));
          line = word.replace(/^\s+/, "");
        }
      }
      if (line.length > 0) {
        result.push(line.replace(/\s+$/, ""));
      }
    }
    return result;
  }

  /* ── Build sidebar column ── */
  function buildSidebar() {
    var rows = [];

    rows.push("<hd>СОСТОЯНИЕ</hd>");
    rows.push("");

    // O2
    var o2Pct = Math.max(0, Math.min(100, state.o2));
    var o2Str = `${o2Pct}%`;
    var o2Tag = o2Pct > 50 ? "bri" : o2Pct > 25 ? "amb" : "red";
    rows.push(cells("O2 LEVEL", `<${o2Tag}>${o2Str}</${o2Tag}>`, SIDE_W));
    var o2Lit = Math.round((o2Pct / 100) * SIDE_W);
    var o2Bar =
      "<bri>" +
      "\u2588".repeat(o2Lit) +
      "</bri>" +
      "<dim>" +
      "\u2591".repeat(SIDE_W - o2Lit) +
      "</dim>";
    rows.push(o2Bar);

    // Morale
    var moralePct = Math.max(0, Math.min(100, state.morale));
    var moraleStr = `${moralePct}%`;
    var moraleTag = moralePct > 50 ? "bri" : moralePct > 25 ? "amb" : "red";
    rows.push(
      cells("MORALE", `<${moraleTag}>${moraleStr}</${moraleTag}>`, SIDE_W),
    );
    var moraleLit = Math.round((moralePct / 100) * SIDE_W);
    var moraleBar =
      "<bri>" +
      "\u2588".repeat(moraleLit) +
      "</bri>" +
      "<dim>" +
      "\u2591".repeat(SIDE_W - moraleLit) +
      "</dim>";
    rows.push(moraleBar);

    rows.push("");
    rows.push("<hd>СИСТЕМЫ</hd>");
    rows.push("");

    // System status lamps (#173). Colors derive from computeLamps() which
    // reads parsed MIRSEND lamp inputs + o2. Defaults reflect the canonical
    // opening (PWR red, LIFE amb, COMM red, NAV amb, HULL grn, DOCK grn)
    // so a fresh shell isn't lying before the first MIRSEND lands.
    //
    // Right cell is padded to a fixed visible width (6 chars = "\u2588 LIFE")
    // so the right-lamp column stays at col 20 regardless of label length \u2014
    // otherwise cells() right-aligns and NAV (3 chars) drifts one column
    // right of LIFE/DOCK (4 chars).
    var lamps = computeLamps();
    var lamp = (k, label) => `<${lamps[k]}>\u2588</${lamps[k]}> ${label}`;
    var rightLamp = (k, label) => {
      var s = lamp(k, label);
      return s + " ".repeat(Math.max(0, 6 - visLen(s)));
    };
    rows.push(cells(lamp("pwr", "PWR"), rightLamp("life", "LIFE"), SIDE_W));
    rows.push(cells(lamp("comm", "COMM"), rightLamp("nav", "NAV"), SIDE_W));
    rows.push(cells(lamp("hull", "HULL"), rightLamp("dock", "DOCK"), SIDE_W));

    rows.push("");
    rows.push("<hd>ИНВЕНТАРЬ</hd>");
    rows.push("");

    if (state.inventory.length === 0) {
      rows.push("<dim>(Nothing carried)</dim>");
    } else {
      for (let i = 0; i < state.inventory.length; i++) {
        let item = state.inventory[i];
        if (item.length > SIDE_W - 2) {
          item = item.substring(0, SIDE_W - 2);
        }
        rows.push(`> ${item}`);
      }
    }

    return rows;
  }

  /* ── Build the visible story rows ── */
  function buildStoryColumn() {
    var totalLines = storyLines.length;
    var maxOffset = Math.max(0, totalLines - BODY_ROWS);
    var offset = Math.min(_storyScrollOffset, maxOffset);
    var end = totalLines - offset;
    var start = Math.max(0, end - BODY_ROWS);
    var rows = [];
    for (let i = start; i < end; i++) {
      rows.push(storyLines[i]);
    }
    while (rows.length < BODY_ROWS) rows.push("");
    return rows;
  }

  /* ── Compose the full 80×25 screen ── */
  function compose() {
    var out = [];
    var storyCol = buildStoryColumn();
    var sideCol = buildSidebar();

    // Top border
    out.push(`\u2554${"\u2550".repeat(TOTAL_W - 2)}\u2557`);

    // Header line. Shows metadata only (location + console + diegetic
    // date/time). Gauges live in the sidebar so we don't double-display.
    var roomLabel = state.currentRoom
      ? escHtml(state.currentRoom.toUpperCase())
      : "TERM-04";
    var header =
      "SYS <bri>\u041C\u0418\u0420-3/" +
      roomLabel +
      "</bri>   " +
      "CONSOLE <bri>04</bri>   " +
      "<bri>17.03.1988</bri>   " +
      "<bri>02:14 \u041C\u0421\u041A</bri>";
    out.push(`\u2551 ${pad(header, HEADER_W)} \u2551`);

    // Separator under header
    out.push(
      "\u2560" +
        "\u2550".repeat(STORY_W + 2) +
        "\u2564" +
        "\u2550".repeat(SIDE_W + 2) +
        "\u2563",
    );

    // Body rows
    var bodyRows = Math.max(storyCol.length, sideCol.length, BODY_ROWS);
    for (let i = 0; i < bodyRows; i++) {
      const left = storyCol[i] || "";
      const right = sideCol[i] || "";
      // storyLines entries are pre-escaped at push-time (see
      // appendStoryText / appendPlayerInput), so trusted tags like <hd>
      // and <echo> survive into the rendered output.
      out.push(
        "\u2551 " +
          pad(left, STORY_W) +
          " \u2502 " +
          pad(right, SIDE_W) +
          " \u2551",
      );
    }

    // Separator above input
    out.push(
      "\u2560" +
        "\u2550".repeat(STORY_W + 2) +
        "\u2567" +
        "\u2550".repeat(SIDE_W + 2) +
        "\u2563",
    );

    // Input line
    var inputText = escHtml(currentInputText);
    var inputLine = `<bri>&gt;</bri> <bri>${inputText}</bri><cur>\u2588</cur>`;
    out.push(`\u2551 ${pad(inputLine, HEADER_W)} \u2551`);

    // Bottom border
    out.push(`\u255A${"\u2550".repeat(TOTAL_W - 2)}\u255D`);

    return out.join("\n");
  }

  /* ── Render the display ── */
  function renderDisplay() {
    if (!displayPre) return;
    displayPre.innerHTML = compose();
    fitDisplay();
  }

  /* ── Auto-scale <pre> to fill screen ── */
  function fitDisplay() {
    if (!displayPre) return;
    var screen = document.getElementById("screen");
    if (!screen) return;
    displayPre.style.fontSize = "10px";
    var rect = displayPre.getBoundingClientRect();
    var cw = screen.clientWidth - 32;
    var ch = screen.clientHeight - 24;
    var scaleW = cw / rect.width;
    var scaleH = ch / rect.height;
    var scale = Math.min(scaleW, scaleH);
    displayPre.style.fontSize = `${10 * scale}px`;
  }

  /* ── Sweeping scanline animation ── */
  function initScanline() {
    var bar = document.getElementById("scan-line");
    var screen = document.getElementById("screen");
    if (!bar || !screen) return;
    function rand(a, b) {
      return a + Math.random() * (b - a);
    }
    function sweep() {
      // Reduced-motion gate (#144). Re-checked per sweep so a live mode
      // change in the Settings dialog snaps the effect off mid-loop
      // rather than requiring a page reload. CSS also hides #scan-line
      // under html.reduced-motion, so this is belt-and-suspenders.
      if (window.MirsEndMotion?.isReduced?.()) {
        bar.style.opacity = "0";
        setTimeout(sweep, 2000);
        return;
      }
      var h = screen.clientHeight;
      var dur = rand(900, 4200);
      var op = rand(0.35, 1.0);
      bar.style.transition = "none";
      bar.style.transform = "translateY(-12px)";
      bar.style.opacity = "0";
      bar.offsetHeight;
      bar.style.transition = `transform ${dur}ms linear, opacity 200ms ease-in`;
      bar.style.opacity = String(op);
      bar.style.transform = `translateY(${h + 8}px)`;
      setTimeout(() => {
        bar.style.opacity = "0";
      }, dur - 180);
      var gap = Math.random() < 0.25 ? rand(150, 600) : rand(2500, 9000);
      setTimeout(sweep, dur + gap);
    }
    setTimeout(sweep, 600);
  }

  /* ── Initialization ── */
  function init() {
    storyOutput = document.getElementById("story-output");
    commandInput = document.getElementById("command-input");
    titleScreen = document.getElementById("title-screen");
    menuContinueBtn = document.getElementById("menu-continue");
    ingameMenuBtn = document.getElementById("ingame-menu-btn");
    displayPre = document.getElementById("display");

    commandInput.addEventListener("keydown", handleKeyDown);
    commandInput.addEventListener("input", handleInputChange);

    /* Restore command history from a previous session if available. */
    loadCommandHistory();

    /* Menu button handlers */
    document
      .getElementById("menu-new-game")
      .addEventListener("click", startNewGame);
    menuContinueBtn.addEventListener("click", continueGame);
    ingameMenuBtn.addEventListener("click", showMenu);

    /* ESC key: close the save/load modal if it is open, otherwise toggle
       the in-game menu. The modal is layered above the menu, so it must
       take ESC priority. */
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        if (window.MirsEndIntro?.isActive()) return;
        if (_saveLoadModalOpen) {
          closeSaveLoadModal();
          return;
        }
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

    /* Scrollback through the story buffer. PageUp/Down step by half a
       screen; Home/End jump to the ends. The hidden #command-input
       captures most keys but ignores these, so the document handler
       sees them. Suppressed during the title screen and intro. */
    document.addEventListener("keydown", (e) => {
      if (!state.gameStarted) return;
      if (window.MirsEndIntro?.isActive()) return;
      if (titleScreen && !titleScreen.classList.contains("hidden")) return;
      if (e.key === "PageUp") {
        e.preventDefault();
        scrollUp(SCROLL_PAGE);
      } else if (e.key === "PageDown") {
        e.preventDefault();
        scrollDown(SCROLL_PAGE);
      } else if (e.key === "Home" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        scrollToTop();
      } else if (e.key === "End" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        scrollToBottom();
      }
    });

    /* Mouse-wheel scrollback over the visible screen. Trackpad gestures
       generate many wheel events per second; deltaY is divided so a
       full notch ≈ 1–2 lines, with a per-event cap so a hard fling
       can't jump past the buffer. */
    var screen = document.getElementById("screen");
    if (screen) {
      screen.addEventListener(
        "wheel",
        (e) => {
          if (!state.gameStarted) return;
          if (titleScreen && !titleScreen.classList.contains("hidden")) return;
          var lines = Math.max(
            1,
            Math.min(BODY_ROWS, Math.round(Math.abs(e.deltaY) / 20)),
          );
          if (e.deltaY < 0) {
            e.preventDefault();
            scrollUp(lines);
          } else if (e.deltaY > 0) {
            e.preventDefault();
            scrollDown(lines);
          }
        },
        { passive: false },
      );
    }

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

    /* Load persisted typing-effect settings (m13 #140). Default is off. */
    loadTypingConfig();

    /* Any key while a typing animation is active reveals the rest of
       the current message immediately. Capture phase so it runs before
       other handlers (command-input typing, scroll keys, menu toggle)
       — those handlers continue to work, the skip just runs alongside. */
    document.addEventListener(
      "keydown",
      () => {
        if (_activeTyping) skipTyping();
      },
      true,
    );

    /* Wire up save/load UI buttons (SaveManager multi-slot system) */
    initSaveLoadButtons();

    /* Record the playtest session on every change to #story-output. */
    initSessionRecorder();

    /* Fetch the version descriptor produced by scripts/make_version.py
       so session payloads can carry the exact code state. */
    loadVersionJson();

    /* Fetch the perception variant bank (m5 #41). */
    loadPerceptionBank();

    /* Check for saved game to enable Continue button */
    checkSavedGame();

    /* Warm AI: badge + first-run onboarding */
    initAiBadge();
    if (AI_ENABLED) {
      showAiOnboardingModal();
    }

    /* Render initial display */
    renderDisplay();

    /* Start animations */
    window.addEventListener("resize", fitDisplay);
    initScanline();

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
    storyLines = [];
    _storyScrollOffset = 0;
    currentInputText = "";

    hideMenu();
    renderDisplay();
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
        if (recent.data.commandHistory !== undefined) {
          state.commandHistory = recent.data.commandHistory;
          state.historyIndex = state.commandHistory.length;
        }
        state.gameStarted = true;
        state.sessionStartedAt =
          state.sessionStartedAt || new Date().toISOString();
        storyOutput.innerHTML = "";
        storyLines = [];
        _storyScrollOffset = 0;
        currentInputText = "";
        hideMenu();
        renderDisplay();
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
    storyLines = [];
    _storyScrollOffset = 0;
    currentInputText = "";

    hideMenu();
    renderDisplay();

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

  function checkProxy() {
    return fetch(AI_PROXY_URL, { method: "HEAD", mode: "no-cors" })
      .then(() => true)
      .catch(() => false);
  }

  function handleArgonCommand() {
    checkProxy().then((reachable) => {
      if (!reachable) {
        console.warn(
          "[MirsEnd] AI proxy unreachable — falling back to canned line.",
        );
        appendStoryText(AI_CANNED_LINE);
        return;
      }
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

  /* ── AI online badge (appended to hidden game-shell) ── */
  function initAiBadge() {
    if (!AI_ENABLED) return;
    var panel = document.getElementById("game-shell");
    if (!panel) return;
    var badge = document.createElement("div");
    badge.id = "ai-status-badge";
    badge.textContent = "AI online";
    panel.appendChild(badge);
  }

  /* ── Command history persistence ── */
  function loadCommandHistory() {
    var raw;
    var parsed;
    try {
      raw = localStorage.getItem(HISTORY_KEY);
      if (raw) {
        parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          state.commandHistory = parsed;
          state.historyIndex = parsed.length;
        }
      }
    } catch (_e) {
      /* localStorage may be unavailable */
    }
  }

  function saveCommandHistory() {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(state.commandHistory));
    } catch (_e) {
      /* localStorage may be unavailable or full */
    }
  }

  /* ── Input change handler — update display on every keystroke ── */
  function handleInputChange() {
    currentInputText = commandInput.value;
    renderDisplay();
  }

  /* ── Command history & input handling ── */
  function handleKeyDown(e) {
    if (e.key === "Enter") {
      const cmd = commandInput.value.trim();
      if (cmd.length === 0) return;

      state.commandHistory.push(cmd);
      state.historyIndex = state.commandHistory.length;
      saveCommandHistory();
      commandInput.value = "";
      currentInputText = "";

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
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (state.historyIndex > 0) {
        state.historyIndex--;
        commandInput.value = state.commandHistory[state.historyIndex];
        currentInputText = commandInput.value;
        renderDisplay();
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
      currentInputText = commandInput.value;
      renderDisplay();
    }
  }

  /* ── Display functions ── */

  // The Inform 7 status line carries the positional fields o2/morale/inv
  // and an extensible trailing block of name=value pairs. Capture inv=...
  // non-greedily and keep the trailing block in group 4 so we can parse
  // forward-compatible lamp inputs (pwr/comm-tx/dock per #173) and other
  // story-state instrumentation (b1/b2/act2) out of it.
  var MIRSEND_STATUS_RE =
    /\[MIRSEND o2=(-?\d+) morale=(-?\d+) inv=(.*?)((?:\s+[\w-]+=[^\]\s]*)*)\]/;

  function interceptAiPrompt(text) {
    if (!window.StationAI) return false;
    var match = window.StationAI.matchAiPromptTag(text);
    if (!match) return false;
    if (!AI_ENABLED) {
      appendStoryText(AI_CANNED_LINE);
      return true;
    }
    window.StationAI.handleAiPrompt(match);
    return true;
  }

  function parseAndApplyMirsendStatus(text) {
    var m = text.match(MIRSEND_STATUS_RE);
    if (!m) return false;
    var o2 = parseInt(m[1], 10);
    var morale = parseInt(m[2], 10);
    var invStr = (m[3] || "").trim();
    var trailing = (m[4] || "").trim();
    var inventory = invStr === "" ? [] : invStr.split(",").map((s) => s.trim());
    state.o2 = o2;
    state.morale = morale;
    state.inventory = inventory;
    parseLampInputs(trailing);
    parseScore(trailing);
    updateStatus();
    return true;
  }

  // Extract score=N from the MIRSEND trailing block (#216 finding 11).
  // The MCP server reads state.score via window.MirsEnd.getScore.
  function parseScore(trailing) {
    var m = /score=(-?\d+)/.exec(trailing);
    if (m) state.score = parseInt(m[1], 10);
  }

  // Extract boolean lamp inputs (pwr/comm-tx/dock) from the MIRSEND trailing
  // key=value block. Each is "0"|"1"; absent fields leave the prior value in
  // place so a transient story.ni emit gap doesn't flicker the lamps.
  function parseLampInputs(trailing) {
    if (!state.lampInputs) state.lampInputs = {};
    var re = /(pwr|comm-tx|dock)=([01])/g;
    var match = re.exec(trailing);
    var key;
    while (match !== null) {
      key = match[1] === "comm-tx" ? "commTx" : match[1];
      state.lampInputs[key] = match[2] === "1";
      match = re.exec(trailing);
    }
  }

  // Derive lamp colors from current ship state. Returns a {pwr,life,comm,
  // nav,hull,dock} map of tag names ("grn"|"amb"|"red"|"off"). Defaults
  // reflect the canonical opening per lib/ship-state.js so the panel reads
  // correctly even before the first MIRSEND lands.
  //
  // Severity convention: grn = nominal, amb = degraded but functional,
  //                      red = actively failed, off = system absent / detached.
  function computeLamps() {
    var i = state.lampInputs || {};
    var lamps = {
      pwr: "red", // main bus offline at opening
      life: "amb", // O2 reserve full but gen offline, LiOH passive
      comm: "red", // no live channel (distress loop only)
      nav: "amb", // no orientation lock without power
      hull: "grn", // breached but sealed — airtight
      dock: "grn", // Soyuz + Progress both docked
    };

    if (i.pwr) lamps.pwr = "grn";

    // LIFE: amber until power restores life support; then track o2 reserve.
    // Even unpowered, drop straight to red on critical o2 — the lamp should
    // scream when the player is actually suffocating.
    if (i.pwr) {
      if (state.o2 > 50) lamps.life = "grn";
      else if (state.o2 > 25) lamps.life = "amb";
      else lamps.life = "red";
    } else if (state.o2 <= 25) {
      lamps.life = "red";
    }

    // COMM: red without power; amber once powered (can receive); green once
    // the player has transmitted (two-way channel established).
    if (i.commTx) lamps.comm = "grn";
    else if (i.pwr) lamps.comm = "amb";

    if (i.pwr) lamps.nav = "grn";

    // DOCK goes off when chose-descent is true (Soyuz detached). story.ni
    // emits dock=0 after that flag flips.
    if (i.dock === false) lamps.dock = "off";

    return lamps;
  }

  /* ── Perception variant overlay (m5 #41) ──
     Inform 7 emits [PERCEIVE key] at the head of variant-eligible descriptions.
     Glulxe/GlkOte may flush the marker and the body paragraph in separate
     stream chunks (the [line break] after the marker forces a flush), so we
     can't always substitute inline. Instead the marker arms a "pending trap"
     that fires on the next chunk with body content, replacing its first
     paragraph with the bucketed variant. Inline marker+body works too —
     the trap fires on the same chunk after the marker is stripped. */

  var PERCEIVE_MARKER_RE = /\[PERCEIVE ([\w-]+)\][ \t]*\n?/g;
  var pendingPerceptionVariant = null;

  function currentBucket() {
    /* Test/dev override hatch (parallels MIRSEND_AI_ENABLED, MIRSEND_PLAYER_KIND). */
    var override =
      typeof window.MIRSEND_PERCEPTION_BUCKET === "string"
        ? window.MIRSEND_PERCEPTION_BUCKET
        : null;
    if (override === "low" || override === "mid" || override === "high") {
      return `morale:${override}`;
    }
    /* Thresholds match the sidebar morale color buckets (>50 / >25 / ≤25). */
    var m = state.morale;
    if (m <= 25) return "morale:low";
    if (m <= 50) return "morale:mid";
    return "morale:high";
  }

  function resolveVariant(key) {
    if (!perceptionBank) return null;
    var variants = perceptionBank[key]?.variants;
    if (!variants) return null;
    var v = variants[currentBucket()];
    return v && v.length > 0 ? v : null;
  }

  function applyPerception(text) {
    /* Strip any markers in this chunk; arm the trap for the next body chunk. */
    text = text.replace(PERCEIVE_MARKER_RE, (_match, key) => {
      var variant = resolveVariant(key);
      if (variant !== null) pendingPerceptionVariant = variant;
      return "";
    });
    /* Fire the trap on the first chunk with body content. */
    if (
      pendingPerceptionVariant !== null &&
      text.replace(/\s+/g, "").length > 0
    ) {
      const v = pendingPerceptionVariant;
      pendingPerceptionVariant = null;
      const firstBreak = text.indexOf("\n\n");
      text = firstBreak === -1 ? v : v + text.slice(firstBreak);
    }
    return text;
  }

  function loadPerceptionBank() {
    fetch("perceptions.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((b) => {
        perceptionBank = b;
      })
      .catch(() => {
        perceptionBank = null;
      });
  }

  function appendStoryText(text) {
    /* Intercept status lines before they reach the DOM. */
    if (parseAndApplyMirsendStatus(text)) return;

    /* Intercept AI-PROMPT tags from Inform 7 and route to Station AI. */
    if (interceptAiPrompt(text)) return;

    /* Substitute perception variants and strip [PERCEIVE …] markers. */
    text = applyPerception(text);

    /* Add to hidden #story-output DOM (for session recording + e2e tests) */
    var span = document.createElement("span");
    span.className = "story-text";
    span.textContent = `${text}\n\n`;
    storyOutput.appendChild(span);

    /* Room-name lines arrive on their own — render as a bright-phosphor
       Cyrillic heading. Latin-only fallback if no Cyrillic gloss exists
       for this room. The bilingual `LATIN / CYRILLIC` treatment was
       dropped because IBM Plex Mono's Cyrillic glyph widths don't match
       its Latin widths, which threw off the 80×25 grid padding whenever
       a Cyrillic gloss sat next to a Latin label. */
    const trimmed = text.trim();
    if (KNOWN_ROOMS.indexOf(trimmed) !== -1) {
      const cyr = ROOM_CYRILLIC[trimmed];
      const heading = cyr
        ? `<hd>${cyr}</hd>`
        : `<hd>${trimmed.toUpperCase()}</hd>`;
      pushStoryLine(heading);
      pushStoryLine("");
      renderDisplay();
      detectRoomChange(text);
      return;
    }

    /* Add to visible story column. Each wrapped line is HTML-escaped
       at push-time so Glulx prose containing <, >, & renders as text
       rather than as injected markup. Trusted tags (room headings,
       echoes, cursor) are pushed pre-formatted via other paths. When
       the optional typing effect is enabled (m13 #140) the message is
       routed through the animation engine, which queues subsequent
       writes to preserve order. */
    var wrapped = wordWrap(text, STORY_W);
    if (typingConfig.enabled) {
      queueOrAnimate(wrapped);
    } else {
      for (let i = 0; i < wrapped.length; i++) {
        pushStoryLine(escHtml(wrapped[i]));
      }
      pushStoryLine(""); // blank line between paragraphs
      renderDisplay();
    }

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

  var _versionString = null;

  function detectGameVersion() {
    if (_versionString) return _versionString;
    const meta = document.querySelector('meta[name="game-version"]');
    return meta ? meta.getAttribute("content") || "unknown" : "unknown";
  }

  /* Branches we treat as "version string is enough." On develop or main,
     no branch suffix appears on the bezel. Anything else gets
     " · <branch>" appended so a side-by-side reviewer can tell at a
     glance which feature branch is being played. */
  var BEZEL_VERSION_TRUNK_BRANCHES = [
    "develop",
    "main",
    "master",
    "HEAD",
    "unknown",
  ];

  function renderBezelVersion(data) {
    var el = document.getElementById("bezel-version");
    if (!el) return;
    if (!data || typeof data.version_string !== "string") return;
    var label = `FW ${data.version_string}`;
    if (
      typeof data.git_branch === "string" &&
      BEZEL_VERSION_TRUNK_BRANCHES.indexOf(data.git_branch) === -1
    ) {
      label += ` · ${data.git_branch}`;
    }
    el.textContent = label;
  }

  function loadVersionJson() {
    fetch("dist/version.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && typeof data.version_string === "string") {
          _versionString = data.version_string;
          const meta = document.querySelector('meta[name="game-version"]');
          if (meta) meta.setAttribute("content", _versionString);
          renderBezelVersion(data);
        }
      })
      .catch(() => {
        /* Ignore: detectGameVersion() falls back to the meta tag, and
           the bezel #brand .version element hides itself when empty. */
      });
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
    /* Hidden DOM for session recording */
    var span = document.createElement("span");
    span.className = "player-input";
    span.textContent = `> ${text}\n`;
    storyOutput.appendChild(span);

    /* Visible story column — show as dim echo. The `>` is pushed as a
       trusted bri-tag; user text is escaped before injection. */
    pushStoryLine(`<echo>&gt; ${escHtml(text)}</echo>`);

    /* Typing a command always returns the viewport to the bottom — the
       player wants to see the response to what they just submitted. */
    scrollToBottom();
  }

  function appendSystemText(text) {
    /* Hidden DOM for session recording */
    var span = document.createElement("span");
    span.className = "system-text";
    span.textContent = `${text}\n`;
    storyOutput.appendChild(span);

    /* Visible story column. Wrapped chunks are escaped at push-time. */
    var wrapped = wordWrap(text, STORY_W);
    for (let i = 0; i < wrapped.length; i++) {
      pushStoryLine(`<dim>${escHtml(wrapped[i])}</dim>`);
    }

    renderDisplay();
  }

  function scrollToBottom() {
    _storyScrollOffset = 0;
    renderDisplay();
  }

  function updateStatus() {
    renderDisplay();
  }

  /* ── Room detection from story output ── */
  function detectRoomChange(text) {
    for (let i = 0; i < KNOWN_ROOMS.length; i++) {
      const room = KNOWN_ROOMS[i];
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

    /* Per-column wipe cutscene on module change (#138). Only on actual room
       change — re-rendering the same room shouldn't trigger it. The cutscene
       runs as an overlay so state and input are preserved; the overlay
       removes its own skip listener on completion so subsequent keys reach
       the game. */
    if (changed && state.currentRoom !== null && window.MirsEndCutscene) {
      try {
        window.MirsEndCutscene.transitionTo(key);
      } catch (_e) {
        /* swallow — a cutscene failure must not block room entry */
      }
    }
  }

  /* ── Scene art loading (cached, fetched on room change) ── */
  function loadSceneArt(key) {
    var path = ROOM_ART[key];
    if (!path) return;

    if (artCache[key]) {
      return;
    }

    fetch(path)
      .then((response) => {
        if (!response.ok) return;
        return response.text();
      })
      .then((text) => {
        if (text) {
          artCache[key] = text;
        }
      })
      .catch(() => {
        /* Silent failure */
      });
  }

  /* ── Interpreter I/O bridge ── */

  function hookInterpreter() {
    if (typeof window.GlkOte !== "undefined") {
      hookGlkOte();
      return;
    }

    if (typeof window.parchment !== "undefined") {
      hookParchment();
      return;
    }

    appendSystemText(
      "[MIR'S END — UI Shell loaded. Waiting for interpreter...]",
    );
    appendSystemText(
      "[Load a Glulx interpreter (Quixe or Parchment) to play the story.]",
    );

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
    observeWindowport();
    appendSystemText("[Interpreter connected.]");
    if (window.MirsEndBoot) {
      window.MirsEndBoot.start();
    }
  }

  function hookParchment() {
    state.interpreterReady = true;
    appendSystemText("[Parchment interpreter connected.]");
  }

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
      const lines = windowport.querySelectorAll(".BufferLine");
      for (let i = 0; i < lines.length; i++) {
        const key = `line-${i}`;
        if (seen.has(key)) continue;
        const text = lines[i].textContent || "";
        // Inform 7 emits a bare ">" prompt buffer line at the end of every
        // turn (with a trailing zero-width joiner U+200D). Our visible UI
        // has its own input row, so the inline prompt is just visual noise.
        // Strip ZWJ + standard whitespace, then drop empty / pure ">" lines.
        const trimmed = text.replace(/[‍​‌﻿]/g, "").trim();
        if (trimmed.length > 0 && trimmed !== ">") {
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

  function sendToInterpreter(cmd) {
    if (state.interpreterReady) {
      const glkInput = document.querySelector("#windowport input.LineInput");
      if (glkInput) {
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

        setTimeout(() => commandInput.focus(), 0);
        setTimeout(() => commandInput.focus(), 50);
        return;
      }
    }
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
          "You are coming to. Your face is wet. Your head hurts. The dark is absolute.\n\nNo hum of ventilation. No green glow of status panels. Just the hammering of your own pulse and a darkness so complete you cannot tell if your eyes are open.\n\nSomething has gone terribly wrong.",
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
  }

  /* ── Save/Load UI ── */

  /* Width (in monospace cells) of the box-drawing frame around the modal.
     Wide enough for the bilingual title plus a comfortable margin. */
  var SAVE_LOAD_FRAME_WIDTH = 56;

  function buildBoxFrameLine(kind, width) {
    var fill = "═".repeat(Math.max(0, width - 2));
    if (kind === "top") return `╔${fill}╗`;
    if (kind === "bottom") return `╚${fill}╝`;
    return `║${" ".repeat(Math.max(0, width - 2))}║`;
  }

  /* Slot label in the v3 style: `SLOT 01 / СЛОТ 01` (or `AUTO / АВТО`). */
  function bilingualSlotLabel(slot) {
    if (slot === "auto") return "AUTO / АВТО";
    var n = String(slot).padStart(2, "0");
    return `SLOT ${n} / СЛОТ ${n}`;
  }

  function showSaveLoadModal(mode) {
    closeSaveLoadModal();
    _saveLoadModalOpen = true;

    var overlay = document.createElement("div");
    overlay.id = "save-load-overlay";
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeSaveLoadModal();
    });

    var modal = document.createElement("div");
    modal.id = "save-load-modal";

    /* Box-drawing frame wraps the entire modal content. The corners and
       edges (╔ ═ ╗ ║ ╚ ╝) are rendered as text inside <pre> blocks so
       they align in IBM Plex Mono. */
    var frame = document.createElement("div");
    frame.className = "save-load-frame";

    var frameTop = document.createElement("pre");
    frameTop.className = "save-load-frame-edge";
    frameTop.textContent = buildBoxFrameLine("top", SAVE_LOAD_FRAME_WIDTH);
    frame.appendChild(frameTop);

    var body = document.createElement("div");
    body.className = "save-load-frame-body";

    var title = document.createElement("h2");
    var titleEn = document.createElement("span");
    titleEn.className = "save-load-title-en";
    titleEn.textContent = mode === "save" ? "SAVE GAME" : "LOAD GAME";
    var titleRu = document.createElement("span");
    titleRu.className = "save-load-title-ru";
    titleRu.textContent = mode === "save" ? "СОХРАНИТЬ ИГРУ" : "ЗАГРУЗИТЬ ИГРУ";
    title.appendChild(titleEn);
    title.appendChild(titleRu);
    body.appendChild(title);

    if (!window.SaveManager?.storageAvailable()) {
      const msg = document.createElement("p");
      msg.className = "save-load-error";
      msg.textContent = `localStorage is not available. Cannot ${mode} games.`;
      body.appendChild(msg);
    } else {
      const slots = window.SaveManager.listSlots();
      for (let i = 0; i < slots.length; i++) {
        ((slot) => {
          const row = document.createElement("div");
          row.className = "save-slot-row";

          const label = document.createElement("span");
          label.className = "save-slot-label";
          label.textContent = bilingualSlotLabel(slot.slot);

          const summary = document.createElement("span");
          summary.className = "save-slot-summary";
          summary.textContent = slot.summary;

          row.appendChild(label);
          row.appendChild(summary);

          if (mode === "save" && slot.slot !== "auto") {
            const saveBtn = document.createElement("button");
            saveBtn.className = "save-slot-btn";
            saveBtn.textContent = "SAVE";
            saveBtn.addEventListener("click", () => {
              const result = window.SaveManager.saveToSlot(slot.slot);
              appendSystemText(`[${result.message}]`);
              closeSaveLoadModal();
            });
            row.appendChild(saveBtn);
          } else if (mode === "load" && slot.hasData) {
            const loadBtn = document.createElement("button");
            loadBtn.className = "save-slot-btn";
            loadBtn.textContent = "LOAD";
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

          body.appendChild(row);
        })(slots[i]);
      }
    }

    var closeBtn = document.createElement("button");
    closeBtn.id = "save-load-close";
    closeBtn.textContent = "CANCEL";
    closeBtn.addEventListener("click", closeSaveLoadModal);
    body.appendChild(closeBtn);

    frame.appendChild(body);

    var frameBottom = document.createElement("pre");
    frameBottom.className = "save-load-frame-edge";
    frameBottom.textContent = buildBoxFrameLine(
      "bottom",
      SAVE_LOAD_FRAME_WIDTH,
    );
    frame.appendChild(frameBottom);

    modal.appendChild(frame);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
  }

  function closeSaveLoadModal() {
    _saveLoadModalOpen = false;
    var existing = document.getElementById("save-load-overlay");
    if (existing) existing.remove();
  }

  function quickSave() {
    if (!window.SaveManager) {
      appendSystemText("[Save system not available.]");
      return;
    }
    var result = window.SaveManager.saveToSlot(1);
    appendSystemText(`[${result.message}]`);
  }

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

  function persistSession() {
    if (!state.gameStarted) return;
    try {
      const session = snapshotSession();
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch (_e) {
      /* localStorage may be unavailable or full — silently ignore. */
    }
  }

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
    scrollUp: scrollUp,
    scrollDown: scrollDown,
    scrollToTop: scrollToTop,
    scrollToBottom: scrollToBottom,
    getScrollOffset: () => _storyScrollOffset,
    getStoryLineCount: () => storyLines.length,
    getLamps: () => computeLamps(),
    getScore: () => state.score || 0,
    getTypingConfig: getTypingConfig,
    setTypingConfig: setTypingConfig,
    skipTyping: skipTyping,
  };

  /* ── Boot ── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
