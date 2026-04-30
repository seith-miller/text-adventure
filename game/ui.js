/**
 * MIR'S END — Web UI Shell
 * Soviet terminal visual language: 80×25 character grid rendered inside
 * a single <pre> element with box-drawing borders and phosphor color tags.
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

  /* ── Terminal grid constants ── */
  var TOTAL_W   = 80;
  var STORY_W   = 48;
  var SIDE_W    = 25;
  var HEADER_W  = 76; // inside outer borders + 1-char pad each side
  var BODY_ROWS = 19; // rows between header separator and input separator
  var MAX_STORY_LINES = 200; // keep scrollback trimmed

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
  var display;        // the <pre id="display">
  var storyOutput;    // hidden #story-output (preserves test contract)
  var commandInput;   // hidden <input id="command-input"> (test contract)
  var titleScreen;
  var menuContinueBtn;
  var ingameMenuBtn;

  /* ── Story line buffer (plain text lines for the story column) ── */
  var storyLines = [];
  var storyScrollOffset = 0; // lines scrolled back from bottom

  /* ── Current input line ── */
  var inputBuffer = "";

  /* ── ASCII art cache ── */
  var artCache = {};

  /* ── Uptime counter ── */
  var uptimeStart = Date.now();

  /* ── Terminal helpers ── */

  /** Strip HTML tags and collapse entities → 1 char for visual length. */
  function visLen(s) {
    return s
      .replace(/<[^>]+>/g, '')
      .replace(/&[a-zA-Z0-9#]+;/g, 'X')
      .length;
  }

  /** Pad string s with spaces to width w (accounting for inline tags). */
  function pad(s, w) {
    var n = w - visLen(s);
    return n > 0 ? s + ' '.repeat(n) : s;
  }

  /** Left + right justified across width w. */
  function cells(left, right, w) {
    var fill = w - visLen(left) - visLen(right);
    return left + ' '.repeat(Math.max(0, fill)) + right;
  }

  /** Word-wrap plain text to fit within a given column width. */
  function wordWrap(text, width) {
    var result = [];
    var paragraphs = text.split('\n');
    for (var p = 0; p < paragraphs.length; p++) {
      var line = paragraphs[p];
      if (line.length === 0) {
        result.push('');
        continue;
      }
      while (line.length > width) {
        var breakAt = line.lastIndexOf(' ', width);
        if (breakAt <= 0) breakAt = width;
        result.push(line.substring(0, breakAt));
        line = line.substring(breakAt + (line[breakAt] === ' ' ? 1 : 0));
      }
      result.push(line);
    }
    return result;
  }

  /** Escape < > & for safe insertion into the <pre> innerHTML. */
  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /* ── Build sidebar column (25 wide × BODY_ROWS) ── */
  function buildSidebar() {
    var rows = [];

    // VITALS header
    rows.push('<hd>VITALS / СОСТОЯНИЕ</hd>');
    rows.push('');

    // O2 bar
    var o2Pct = Math.max(0, Math.min(100, state.o2));
    var o2Tag = o2Pct > 50 ? 'bri' : (o2Pct > 25 ? 'amb' : 'red');
    var o2Str = '<' + o2Tag + '>' + o2Pct + '%</' + o2Tag + '>';
    rows.push(cells('O2 LEVEL', o2Str, SIDE_W));
    var o2Lit = Math.round(o2Pct / 100 * SIDE_W);
    var o2Dim = SIDE_W - o2Lit;
    rows.push('<' + o2Tag + '>' + '█'.repeat(o2Lit) + '</' + o2Tag + '>' +
              '<dim>' + '░'.repeat(o2Dim) + '</dim>');

    // Morale bar
    var moralePct = Math.max(0, Math.min(100, state.morale));
    var mTag = moralePct > 50 ? 'bri' : (moralePct > 25 ? 'amb' : 'red');
    var mStr = '<' + mTag + '>' + moralePct + '%</' + mTag + '>';
    rows.push(cells('MORALE', mStr, SIDE_W));
    var mLit = Math.round(moralePct / 100 * SIDE_W);
    var mDim = SIDE_W - mLit;
    rows.push('<' + mTag + '>' + '█'.repeat(mLit) + '</' + mTag + '>' +
              '<dim>' + '░'.repeat(mDim) + '</dim>');

    rows.push('');

    // SYSTEMS header
    rows.push('<hd>SYSTEMS / СИСТЕМЫ</hd>');
    rows.push('');
    rows.push('<grn>█</grn> PWR              <grn>█</grn> LIFE');
    rows.push('<amb>█</amb> COMM             <off>█</off> NAV');
    rows.push('<red>█</red> HULL             <wht>█</wht> DOCK');
    rows.push('');

    // INVENTORY header
    rows.push('<hd>INVENTORY / ИНВЕНТАРЬ</hd>');
    rows.push('');

    if (state.inventory.length === 0) {
      rows.push('<dim>(nothing carried)</dim>');
    } else {
      for (var i = 0; i < state.inventory.length; i++) {
        var item = state.inventory[i];
        if (item.length > SIDE_W - 2) item = item.substring(0, SIDE_W - 2);
        rows.push('&gt; ' + esc(item));
      }
    }

    return rows;
  }

  /* ── Build the full 80×25 screen ── */
  function compose() {
    var out = [];

    // Row 1: top border
    out.push('╔' + '═'.repeat(TOTAL_W - 2) + '╗');

    // Row 2: header status bar
    var now = new Date();
    var elapsed = Math.floor((Date.now() - uptimeStart) / 1000);
    var uh = String(Math.floor(elapsed / 3600)).padStart(3, '0');
    var um = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
    var us = String(elapsed % 60).padStart(2, '0');
    var hh = String(now.getUTCHours()).padStart(2, '0');
    var mm = String(now.getUTCMinutes()).padStart(2, '0');
    var ss = String(now.getUTCSeconds()).padStart(2, '0');

    var header =
      'SYS <bri>МИР-2/TERM-04</bri>   ' +
      'UPT <bri>' + uh + ':' + um + ':' + us + '</bri>   ' +
      'ORB <bri>412KM/91.2MIN</bri>   ' +
      'TIME <bri>' + hh + ':' + mm + ':' + ss + ' МСК</bri>';
    out.push('║ ' + pad(header, HEADER_W) + ' ║');

    // Row 3: separator (heavy horizontal, light vertical junction)
    out.push('╠' + '═'.repeat(STORY_W + 2) + '╤' + '═'.repeat(SIDE_W + 2) + '╣');

    // Rows 4–22: body (story left, sidebar right)
    var sidebar = buildSidebar();

    // Get visible story lines (last BODY_ROWS lines, adjusted by scroll offset)
    var visibleStory = [];
    var totalStory = storyLines.length;
    var endIdx = totalStory - storyScrollOffset;
    var startIdx = Math.max(0, endIdx - BODY_ROWS);
    for (var i = startIdx; i < endIdx && i < totalStory; i++) {
      visibleStory.push(storyLines[i]);
    }

    for (var r = 0; r < BODY_ROWS; r++) {
      var left = visibleStory[r] || '';
      var right = sidebar[r] || '';
      // Truncate story lines that exceed column width (visual)
      if (visLen(left) > STORY_W) {
        // Simple truncation for plain-text lines
        left = left.substring(0, STORY_W);
      }
      out.push('║ ' + pad(left, STORY_W) + ' │ ' + pad(right, SIDE_W) + ' ║');
    }

    // Row 23: separator above input
    out.push('╠' + '═'.repeat(STORY_W + 2) + '╧' + '═'.repeat(SIDE_W + 2) + '╣');

    // Row 24: input line
    var inputLine = '<bri>&gt;</bri> ' + esc(inputBuffer) + '<cur>█</cur>';
    out.push('║ ' + pad(inputLine, HEADER_W) + ' ║');

    // Row 25: bottom border
    out.push('╚' + '═'.repeat(TOTAL_W - 2) + '╝');

    return out.join('\n');
  }

  /** Render the terminal display and auto-scale to fit. */
  function render() {
    if (!display) return;
    display.innerHTML = compose();
    fit();
  }

  /** Auto-scale the <pre> to fill the screen area. */
  function fit() {
    var pre = display;
    var screen = document.getElementById('screen');
    if (!pre || !screen) return;
    // Reset to a baseline size and measure
    pre.style.fontSize = '10px';
    var rect = pre.getBoundingClientRect();
    var cw = screen.clientWidth  - 32;
    var ch = screen.clientHeight - 24;
    var scaleW = cw / rect.width;
    var scaleH = ch / rect.height;
    var scale = Math.min(scaleW, scaleH);
    pre.style.fontSize = (10 * scale) + 'px';
  }

  /* ── Sweeping scanline animation ── */
  function initScanline() {
    var bar = document.getElementById('scan-line');
    var screen = document.getElementById('screen');
    if (!bar || !screen) return;
    function rand(a, b) { return a + Math.random() * (b - a); }
    function sweep() {
      var h = screen.clientHeight;
      var dur = rand(900, 4200);
      var op = rand(0.35, 1.0);
      bar.style.transition = 'none';
      bar.style.transform = 'translateY(-12px)';
      bar.style.opacity = '0';
      bar.offsetHeight; // force reflow
      bar.style.transition = 'transform ' + dur + 'ms linear, opacity 200ms ease-in';
      bar.style.opacity = String(op);
      bar.style.transform = 'translateY(' + (h + 8) + 'px)';
      setTimeout(function() { bar.style.opacity = '0'; }, dur - 180);
      var gap = Math.random() < 0.25 ? rand(150, 600) : rand(2500, 9000);
      setTimeout(sweep, dur + gap);
    }
    setTimeout(sweep, 600);
  }

  /* ── Initialization ── */
  function init() {
    display = document.getElementById("display");
    storyOutput = document.getElementById("story-output");
    commandInput = document.getElementById("command-input");
    titleScreen = document.getElementById("title-screen");
    menuContinueBtn = document.getElementById("menu-continue");
    ingameMenuBtn = document.getElementById("ingame-menu-btn");

    /* Keyboard input: capture globally and route to the terminal input buffer.
       Also keep the hidden #command-input in sync for test compatibility. */
    document.addEventListener("keydown", handleGlobalKeyDown);

    /* Sync inputBuffer from #command-input whenever its value changes.
       This covers Playwright's fill() (which fires 'input') and normal typing. */
    commandInput.addEventListener("input", function() {
      inputBuffer = commandInput.value;
      render();
    });

    /* Also listen on #command-input for Enter key from tests that press() on it. */
    commandInput.addEventListener("keydown", handleCommandInputKeyDown);

    /* Menu button handlers */
    document
      .getElementById("menu-new-game")
      .addEventListener("click", startNewGame);
    menuContinueBtn.addEventListener("click", continueGame);
    ingameMenuBtn.addEventListener("click", showMenu);

    /* ESC key to toggle menu during gameplay */
    document.addEventListener("keydown", function(e) {
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

    /* Focus the hidden input on click so mobile keyboards work, and so
       Playwright's fill() path functions correctly. */
    document.addEventListener("click", function(e) {
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

    /* Wire up save/load UI buttons (SaveManager multi-slot system) */
    initSaveLoadButtons();

    /* Record the playtest session on every change to #story-output. */
    initSessionRecorder();

    /* Check for saved game to enable Continue button */
    checkSavedGame();

    /* Show title screen on launch */
    showMenu();

    /* Start scanline animation */
    initScanline();

    /* Resize handler */
    window.addEventListener("resize", function() { if (state.gameStarted) render(); });

    /* Periodic header clock update */
    setInterval(function() { if (state.gameStarted) render(); }, 5000);
  }

  /* ── Input handling ── */

  /** Handle keyboard globally for the terminal input buffer. */
  function handleGlobalKeyDown(e) {
    // Don't capture when title screen is up or modal is open
    if (!state.gameStarted) return;
    if (titleScreen && !titleScreen.classList.contains("hidden")) return;
    if (_saveLoadModalOpen) return;

    // Ignore modifier combos except Shift
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    if (e.key === "Enter") {
      /* If the target is #command-input, let handleCommandInputKeyDown
         handle it to avoid double-submit. */
      if (e.target === commandInput) return;
      /* Sync from #command-input.value in case it was set programmatically. */
      if (commandInput.value && commandInput.value !== inputBuffer) {
        inputBuffer = commandInput.value;
      }
      submitCommand();
      e.preventDefault();
    } else if (e.key === "Backspace") {
      if (e.target === commandInput) return; // let 'input' event handle it
      if (inputBuffer.length > 0) {
        inputBuffer = inputBuffer.slice(0, -1);
        commandInput.value = inputBuffer;
        render();
      }
      e.preventDefault();
    } else if (e.key === "ArrowUp") {
      if (state.historyIndex > 0) {
        state.historyIndex--;
        inputBuffer = state.commandHistory[state.historyIndex];
        commandInput.value = inputBuffer;
        render();
      }
      e.preventDefault();
    } else if (e.key === "ArrowDown") {
      if (state.historyIndex < state.commandHistory.length - 1) {
        state.historyIndex++;
        inputBuffer = state.commandHistory[state.historyIndex];
        commandInput.value = inputBuffer;
        render();
      } else {
        state.historyIndex = state.commandHistory.length;
        inputBuffer = "";
        commandInput.value = "";
        render();
      }
      e.preventDefault();
    } else if (e.key.length === 1) {
      /* If the event target is #command-input, the 'input' event handler
         will sync inputBuffer from .value — don't double-add here. */
      if (e.target === commandInput) return;
      inputBuffer += e.key;
      commandInput.value = inputBuffer;
      render();
    }
  }

  /**
   * Handle keydown on the hidden #command-input.
   * This path is used by Playwright tests that do cmdInput.fill("cmd")
   * then cmdInput.press("Enter"). The fill() sets the value directly
   * without firing individual key events, so we sync from .value here.
   */
  function handleCommandInputKeyDown(e) {
    if (e.key === "Enter") {
      /* Sync inputBuffer from .value in case Playwright used fill(). */
      if (commandInput.value && commandInput.value !== inputBuffer) {
        inputBuffer = commandInput.value;
      }
      submitCommand();
      e.preventDefault();
      e.stopPropagation(); // prevent double-handling by global listener
    }
  }

  function submitCommand() {
    var cmd = inputBuffer.trim();
    if (cmd.length === 0) return;

    state.commandHistory.push(cmd);
    state.historyIndex = state.commandHistory.length;
    inputBuffer = "";
    commandInput.value = "";

    appendPlayerInput(cmd);
    sendToInterpreter(cmd);
    render();
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
        render();
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

    /* Clear story */
    storyLines = [];
    storyScrollOffset = 0;
    inputBuffer = "";
    commandInput.value = "";
    storyOutput.innerHTML = "";
    uptimeStart = Date.now();

    hideMenu();
    render();

    /* Play intro sequence if available, then hook the interpreter */
    if (window.MirsEndIntro) {
      window.MirsEndIntro.run(function() {
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
      var recent = window.SaveManager.getMostRecentSave();
      if (recent) {
        window.SaveManager.applyState(recent.data);
        if (recent.data.commandHistory !== undefined) {
          state.commandHistory = recent.data.commandHistory;
          state.historyIndex = state.commandHistory.length;
        }
        state.gameStarted = true;
        state.sessionStartedAt =
          state.sessionStartedAt || new Date().toISOString();
        storyLines = [];
        storyScrollOffset = 0;
        storyOutput.innerHTML = "";
        hideMenu();
        render();
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

    storyLines = [];
    storyScrollOffset = 0;
    storyOutput.innerHTML = "";

    hideMenu();
    render();

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

  /* ── Display functions ── */

  /**
   * Match the machine-readable status line emitted by Inform 7.
   * Format: [MIRSEND o2=N morale=N inv=a,b,c]
   */
  var MIRSEND_STATUS_RE = /\[MIRSEND o2=(-?\d+) morale=(-?\d+) inv=([^\]]*)\]/;

  function parseAndApplyMirsendStatus(text) {
    var m = text.match(MIRSEND_STATUS_RE);
    if (!m) return false;
    var o2 = parseInt(m[1], 10);
    var morale = parseInt(m[2], 10);
    var invStr = (m[3] || "").trim();
    var inventory = invStr === "" ? [] : invStr.split(",").map(function(s) { return s.trim(); });
    state.o2 = o2;
    state.morale = morale;
    state.inventory = inventory;
    render();
    return true;
  }

  function appendStoryText(text) {
    /* Intercept status lines before they reach the display. */
    if (parseAndApplyMirsendStatus(text)) return;

    /* Add to hidden #story-output for test compatibility. */
    var span = document.createElement("span");
    span.className = "story-text";
    span.textContent = text + "\n\n";
    storyOutput.appendChild(span);

    /* Word-wrap and add to story line buffer. */
    var wrapped = wordWrap(text, STORY_W);
    for (var i = 0; i < wrapped.length; i++) {
      storyLines.push(esc(wrapped[i]));
    }
    storyLines.push(''); // blank line between paragraphs
    trimStoryBuffer();
    storyScrollOffset = 0;
    detectRoomChange(text);
    render();
  }

  function appendPlayerInput(text) {
    /* Hidden #story-output for tests. */
    var span = document.createElement("span");
    span.className = "player-input";
    span.textContent = "> " + text + "\n";
    storyOutput.appendChild(span);

    /* Echo into the terminal story column. */
    storyLines.push('<echo>&gt; ' + esc(text) + '</echo>');
    trimStoryBuffer();
    storyScrollOffset = 0;
    render();
  }

  function appendSystemText(text) {
    /* Hidden #story-output for tests. */
    var span = document.createElement("span");
    span.className = "system-text";
    span.textContent = text + "\n";
    storyOutput.appendChild(span);

    storyLines.push('<dim>' + esc(text) + '</dim>');
    trimStoryBuffer();
    storyScrollOffset = 0;
    render();
  }

  function trimStoryBuffer() {
    if (storyLines.length > MAX_STORY_LINES) {
      storyLines = storyLines.slice(storyLines.length - MAX_STORY_LINES);
    }
  }

  /* ── Room detection from story output ── */
  function detectRoomChange(text) {
    for (var i = 0; i < KNOWN_ROOMS.length; i++) {
      var room = KNOWN_ROOMS[i];
      if (
        text.indexOf(room) !== -1 &&
        (text.indexOf(room + "\n") !== -1 ||
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

    /* Auto-save when entering a new area */
    if (changed && window.SaveManager) {
      var result = window.SaveManager.autoSave();
      if (result.success) {
        appendSystemText("[Auto-saved]");
      }
    }
  }

  /* ── Status update (no-op for DOM elements, state is rendered in compose()) ── */
  function updateStatus() {
    render();
  }

  /* ── Scene art loading (kept for compatibility, art not displayed in new UI) ── */
  function loadSceneArt(key) {
    var path = ROOM_ART[key];
    if (!path) return;
    if (artCache[key]) return;
    fetch(path)
      .then(function(response) {
        if (!response.ok) return;
        return response.text();
      })
      .then(function(text) {
        if (text) artCache[key] = text;
      })
      .catch(function() {});
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
    var pollInterval = setInterval(function() {
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

    var flush = function() {
      var lines = windowport.querySelectorAll(".BufferLine");
      for (var i = 0; i < lines.length; i++) {
        var key = "line-" + i;
        if (seen.has(key)) continue;
        var text = lines[i].textContent || "";
        if (text.trim().length > 0) {
          appendStoryText(text);
        }
        seen.add(key);
      }
    };

    var observer = new MutationObserver(function() {
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
    var text = "";
    for (var i = 0; i < content.length; i++) {
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
      var glkInput = document.querySelector("#windowport input.LineInput");
      if (glkInput) {
        glkInput.value = cmd;
        glkInput.focus();

        var native = new KeyboardEvent("keydown", {
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
          var $input = window.jQuery(glkInput);
          var jqEvt = window.jQuery.Event("keydown", {
            keyCode: 13,
            which: 13,
            key: "Enter",
          });
          $input.trigger(jqEvt);
        }

        setTimeout(function() { commandInput.focus(); }, 0);
        setTimeout(function() { commandInput.focus(); }, 50);
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
          "You wake to nothing.\n\nNo hum of ventilation. No green glow of status panels. Just the hammering of your own pulse and a darkness so complete you cannot tell if your eyes are open.\n\nSomething has gone terribly wrong.",
        );
      } else {
        appendStoryText("You look around " + state.currentRoom + ".");
      }
    } else if (lower === "inventory" || lower === "i") {
      if (state.inventory.length === 0) {
        appendStoryText("You are carrying nothing.");
      } else {
        appendStoryText("You are carrying:\n  " + state.inventory.join("\n  "));
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

  function showSaveLoadModal(mode) {
    closeSaveLoadModal();
    _saveLoadModalOpen = true;

    var overlay = document.createElement("div");
    overlay.id = "save-load-overlay";
    overlay.addEventListener("click", function(e) {
      if (e.target === overlay) closeSaveLoadModal();
    });

    var modal = document.createElement("div");
    modal.id = "save-load-modal";

    var title = document.createElement("h2");
    title.textContent = mode === "save" ? "Save Game" : "Load Game";
    modal.appendChild(title);

    if (!window.SaveManager?.storageAvailable()) {
      var msg = document.createElement("p");
      msg.className = "save-load-error";
      msg.textContent = "localStorage is not available. Cannot " + mode + " games.";
      modal.appendChild(msg);
    } else {
      var slots = window.SaveManager.listSlots();
      for (var i = 0; i < slots.length; i++) {
        (function(slot) {
          var row = document.createElement("div");
          row.className = "save-slot-row";

          var label = document.createElement("span");
          label.className = "save-slot-label";
          label.textContent =
            slot.slot === "auto" ? "Auto-save" : "Slot " + slot.slot;

          var summary = document.createElement("span");
          summary.className = "save-slot-summary";
          summary.textContent = slot.summary;

          row.appendChild(label);
          row.appendChild(summary);

          if (mode === "save" && slot.slot !== "auto") {
            var saveBtn = document.createElement("button");
            saveBtn.className = "save-slot-btn";
            saveBtn.textContent = "Save";
            saveBtn.addEventListener("click", function() {
              var result = window.SaveManager.saveToSlot(slot.slot);
              appendSystemText("[" + result.message + "]");
              closeSaveLoadModal();
            });
            row.appendChild(saveBtn);
          } else if (mode === "load" && slot.hasData) {
            var loadBtn = document.createElement("button");
            loadBtn.className = "save-slot-btn";
            loadBtn.textContent = "Load";
            loadBtn.addEventListener("click", function() {
              var result;
              if (slot.slot === "auto") {
                result = window.SaveManager.loadAutoSave();
              } else {
                result = window.SaveManager.loadFromSlot(slot.slot);
              }
              if (result.success) {
                window.SaveManager.applyState(result.data);
                appendSystemText("[" + result.message + "]");
              } else {
                appendSystemText("[" + result.message + "]");
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

  function quickSave() {
    if (!window.SaveManager) {
      appendSystemText("[Save system not available.]");
      return;
    }
    var result = window.SaveManager.saveToSlot(1);
    appendSystemText("[" + result.message + "]");
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

  /* ── Wire up save/load/export buttons ── */
  function initSaveLoadButtons() {
    var saveBtn = document.getElementById("btn-save");
    var loadBtn = document.getElementById("btn-load");
    var continueBtn = document.getElementById("btn-continue");
    var exportBtn = document.getElementById("btn-export");

    if (saveBtn) {
      saveBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        showSaveLoadModal("save");
      });
    }
    if (loadBtn) {
      loadBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        showSaveLoadModal("load");
      });
    }
    if (continueBtn) {
      continueBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        continueGame();
      });
    }
    if (exportBtn) {
      exportBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        downloadSession();
      });
    }
    /* Ctrl+E / Cmd+E anywhere on the page exports too. */
    document.addEventListener("keydown", function(e) {
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
      var session = snapshotSession();
      localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    } catch (_e) {
      /* localStorage may be unavailable or full */
    }
  }

  function initSessionRecorder() {
    if (!storyOutput) return;
    var observer = new MutationObserver(function() {
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
    var json = JSON.stringify(session, null, 2);
    var blob = new Blob([json], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    var stamp = (session.startedAt || new Date().toISOString()).replace(
      /[:.]/g,
      "-",
    );
    a.href = url;
    a.download = "mirsend-session-" + stamp + ".json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    appendSystemText("[Session exported.]");
  }

  /* ── Public API for interpreter integration ── */
  window.MirsEnd = {
    appendStoryText: appendStoryText,
    appendPlayerInput: appendPlayerInput,
    appendSystemText: appendSystemText,
    setCurrentRoom: setCurrentRoom,
    updateStatus: updateStatus,
    getState: function() { return state; },
    setState: function(newState) {
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
    showSaveModal: function() { showSaveLoadModal("save"); },
    showLoadModal: function() { showSaveLoadModal("load"); },
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
