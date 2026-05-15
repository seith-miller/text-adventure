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
    /* shipStatus mirrors a subset of lib/ship-state.js (#72).
       null = no ship-state available yet; lamps render the static fallback
       colors so an early-init render does not show six identical lamps.
       Populated either by MIRSEND extension fields or MirsEnd.setShipStatus. */
    shipStatus: null,
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
  var lampEls; // map of lamp-id → element, populated in init()

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
    initLampEls();

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

    /* Clear story output */
    storyOutput.innerHTML = "";

    hideMenu();
    updateStatus();
    loadSceneArt("darkness");

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

  /* ── Command history & input handling ── */
  function handleKeyDown(e) {
    if (e.key === "Enter") {
      const cmd = commandInput.value.trim();
      if (cmd.length === 0) return;

      state.commandHistory.push(cmd);
      state.historyIndex = state.commandHistory.length;
      commandInput.value = "";

      appendPlayerInput(cmd);
      sendToInterpreter(cmd);
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
   *
   * The body is matched permissively so future fields (e.g. lamp-pwr=on,
   * hull=breach) can be added on the Inform side without breaking the
   * existing parser. parseMirsendBody extracts known fields by name from
   * the captured body string.
   */
  var MIRSEND_STATUS_RE = /\[MIRSEND ([^\]]*)\]/;

  function parseMirsendBody(body) {
    var out = {};
    /* o2 / morale are required by the v1 contract. */
    var m = body.match(/o2=(-?\d+)/);
    if (m) out.o2 = parseInt(m[1], 10);
    m = body.match(/morale=(-?\d+)/);
    if (m) out.morale = parseInt(m[1], 10);
    /* Forward-compatible lamp / ship-state extension fields. Inform 7 may
       add any of these in the same MIRSEND line in a future story.ni change;
       absence here means "not provided this turn" and the lamp retains its
       last known value (or the static fallback). These must come BEFORE
       inv in the MIRSEND line so inv= can match greedily — printed-name
       inventory items can contain spaces (e.g. "Yevgenia's flight
       notebook"). */
    m = body.match(/pwr=([a-z_-]+)/);
    if (m) out.pwr = m[1];
    m = body.match(/hull=([a-z_-]+)/);
    if (m) out.hull = m[1];
    m = body.match(/comm=([a-z_-]+)/);
    if (m) out.comm = m[1];
    m = body.match(/nav=([a-z_-]+)/);
    if (m) out.nav = m[1];
    m = body.match(/dock=([a-z_-]+)/);
    if (m) out.dock = m[1];
    /* inv last: greedily takes the rest of the body so multi-word
       printed names survive intact. */
    m = body.match(/inv=(.*)$/);
    if (m) out.inv = m[1];
    return out;
  }

  function parseAndApplyMirsendStatus(text) {
    var m = text.match(MIRSEND_STATUS_RE);
    if (!m) return false;
    var fields = parseMirsendBody(m[1]);
    var invStr;
    var s;
    if (typeof fields.o2 === "number") state.o2 = fields.o2;
    if (typeof fields.morale === "number") state.morale = fields.morale;
    if (typeof fields.inv === "string") {
      invStr = fields.inv.trim();
      state.inventory =
        invStr === "" ? [] : invStr.split(",").map((s) => s.trim());
    }
    /* If any lamp/ship-state field is present, lift it into shipStatus
       using the lib/ship-state.js shape so updateLamps() reads from one
       source regardless of who populated it. */
    if (fields.pwr || fields.hull || fields.comm || fields.nav || fields.dock) {
      s = state.shipStatus || {};
      if (fields.pwr) {
        s.power = s.power || {};
        s.power.main_bus = fields.pwr === "on" ? "online" : "offline";
      }
      if (fields.hull) {
        s.hull = s.hull || {};
        /* intact | sealed | vented */
        s.hull.central_node =
          fields.hull === "vented"
            ? "vented"
            : fields.hull === "intact"
              ? "intact"
              : "breached, sealed";
      }
      if (fields.comm) {
        s.comms = s.comms || { contacts: { freedom_station: {} } };
        s.comms.contacts = s.comms.contacts || { freedom_station: {} };
        s.comms.contacts.freedom_station =
          s.comms.contacts.freedom_station || {};
        if (fields.comm === "live") {
          s.comms.contacts.freedom_station.live_channel = true;
          s.comms.array = "patched to isolated bus";
        } else if (fields.comm === "static") {
          s.comms.contacts.freedom_station.live_channel = false;
          s.comms.array = "patched to isolated bus";
        } else {
          s.comms.contacts.freedom_station.live_channel = false;
          s.comms.array = "offline";
        }
      }
      if (fields.nav) {
        s.nav = s.nav || {};
        s.nav.orientation_lock = fields.nav === "locked" ? "held" : "drifting";
      }
      if (fields.dock) {
        s.docked = s.docked || {};
        if (fields.dock === "locked") {
          s.docked.soyuz = "nominal";
          s.docked.soft_lock = true;
        } else if (fields.dock === "docked") {
          s.docked.soyuz = "nominal";
          s.docked.soft_lock = false;
        } else {
          s.docked.soyuz = "detached";
          s.docked.soft_lock = false;
        }
      }
      state.shipStatus = s;
    }
    updateStatus();
    return true;
  }

  function appendStoryText(text) {
    /* Intercept status lines before they reach the DOM. */
    if (parseAndApplyMirsendStatus(text)) return;
    var span = document.createElement("span");
    span.className = "story-text";
    span.textContent = `${text}\n\n`;
    storyOutput.appendChild(span);
    scrollToBottom();
    detectRoomChange(text);
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

    updateLamps();
  }

  /* ── System status lamps ──
   *
   * Six lamps reflect real ship state. The shape mirrors lib/ship-state.js
   * (#72). Each lamp picks a color class from the existing palette:
   * grn / amb / red / wht / off (no new tag classes).
   *
   * When state.shipStatus is null (early init, no ship-state available)
   * the lamps render their static fallback colors so the panel does not
   * show six identical lamps. LIFE is special: even with no shipStatus
   * we derive it from o2 because o2 is always present in MIRSEND v1.
   *
   * Mapping (from #173):
   *   PWR  — power.main_bus              online → grn, offline → off
   *   LIFE — life_support / o2           nominal → grn, degraded → amb, failing → red
   *   COMM — comms / freedom_station     live → grn, static → amb, offline → off
   *   NAV  — nav.orientation_lock        held → grn, drifting → amb
   *   HULL — hull.central_node           intact → grn, breach-sealed → amb, vented → red
   *   DOCK — docked.soyuz + soft_lock    locked → wht, docked → amb, detached → off
   */

  var LAMP_FALLBACK = {
    pwr: "lamp-grn",
    life: "lamp-grn",
    comm: "lamp-amb",
    nav: "lamp-off",
    hull: "lamp-red",
    dock: "lamp-wht",
  };

  var LAMP_COLOR_CLASSES = [
    "lamp-grn",
    "lamp-amb",
    "lamp-red",
    "lamp-wht",
    "lamp-off",
  ];

  function initLampEls() {
    lampEls = {
      pwr: document.getElementById("lamp-pwr"),
      life: document.getElementById("lamp-life"),
      comm: document.getElementById("lamp-comm"),
      nav: document.getElementById("lamp-nav"),
      hull: document.getElementById("lamp-hull"),
      dock: document.getElementById("lamp-dock"),
    };
  }

  function setLampColor(id, colorClass) {
    var el = lampEls[id];
    var i;
    if (!el) return;
    for (i = 0; i < LAMP_COLOR_CLASSES.length; i++) {
      el.classList.remove(LAMP_COLOR_CLASSES[i]);
    }
    el.classList.add(colorClass);
    el.dataset.color = colorClass.replace("lamp-", "");
  }

  function deriveLifeColor(s) {
    var o2gen;
    var co2;
    if (s && s.life_support) {
      o2gen = s.life_support.o2_generator;
      co2 = s.life_support.co2_trend;
      if (o2gen === "online" && (co2 === "stable" || co2 === "rising slow")) {
        return "lamp-grn";
      }
      if (co2 === "critical") return "lamp-red";
      return "lamp-amb";
    }
    /* Derived from o2 when no shipStatus.life_support — MIRSEND v1
       contract guarantees o2 is present every turn. */
    if (state.o2 > 50) return "lamp-grn";
    if (state.o2 > 25) return "lamp-amb";
    return "lamp-red";
  }

  function deriveLampColors() {
    var s = state.shipStatus;
    if (!s) {
      /* No ship-state yet — keep the documented static fallback so an
         early-init render does not show six identical lamps. LIFE still
         derives from o2 because o2 is part of MIRSEND v1. */
      return Object.assign({}, LAMP_FALLBACK, { life: deriveLifeColor(null) });
    }
    var out = {};
    var fs;
    var soyuz;

    /* PWR */
    out.pwr =
      s.power && s.power.main_bus === "online" ? "lamp-grn" : "lamp-off";

    /* LIFE */
    out.life = deriveLifeColor(s);

    /* COMM */
    if (s.comms && s.comms.contacts && s.comms.contacts.freedom_station) {
      fs = s.comms.contacts.freedom_station;
      if (fs.live_channel) {
        out.comm = "lamp-grn";
      } else if (s.comms.array && s.comms.array !== "offline") {
        out.comm = "lamp-amb";
      } else {
        out.comm = "lamp-off";
      }
    } else {
      out.comm = LAMP_FALLBACK.comm;
    }

    /* NAV */
    if (s.nav && s.nav.orientation_lock) {
      out.nav = s.nav.orientation_lock === "held" ? "lamp-grn" : "lamp-amb";
    } else if (s.power && s.power.main_bus === "online") {
      out.nav = "lamp-grn";
    } else {
      out.nav = LAMP_FALLBACK.nav;
    }

    /* HULL */
    if (s.hull && s.hull.central_node) {
      if (s.hull.central_node === "intact") out.hull = "lamp-grn";
      else if (s.hull.central_node === "vented") out.hull = "lamp-red";
      else out.hull = "lamp-amb"; /* "breached, sealed" or similar */
    } else {
      out.hull = LAMP_FALLBACK.hull;
    }

    /* DOCK */
    if (s.docked) {
      soyuz = s.docked.soyuz;
      if (soyuz === "detached") {
        out.dock = "lamp-off";
      } else if (s.docked.soft_lock) {
        out.dock = "lamp-wht";
      } else {
        out.dock = "lamp-amb";
      }
    } else {
      out.dock = LAMP_FALLBACK.dock;
    }

    return out;
  }

  function updateLamps() {
    if (!lampEls || !lampEls.pwr) return; /* DOM not ready */
    var colors = deriveLampColors();
    setLampColor("pwr", colors.pwr);
    setLampColor("life", colors.life);
    setLampColor("comm", colors.comm);
    setLampColor("nav", colors.nav);
    setLampColor("hull", colors.hull);
    setLampColor("dock", colors.dock);
  }

  /**
   * Public API: set the ship-status shape directly. Used by tests and by
   * any future module that maintains a richer ship-state object outside
   * the MIRSEND line. Re-renders on the same path as O2 / morale / inv.
   */
  function setShipStatus(newStatus) {
    state.shipStatus = newStatus || null;
    updateStatus();
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
      if (newState.shipStatus !== undefined)
        state.shipStatus = newState.shipStatus;
      updateStatus();
    },
    setShipStatus: setShipStatus,
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
