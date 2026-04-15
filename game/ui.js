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
  };

  /* ── Save key for localStorage ── */
  var SAVE_KEY = "mirsend_save";

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
    document.getElementById("menu-new-game").addEventListener("click", startNewGame);
    menuContinueBtn.addEventListener("click", continueGame);
    ingameMenuBtn.addEventListener("click", showMenu);

    /* ESC key to toggle menu during gameplay */
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        if (state.gameStarted && titleScreen && !titleScreen.classList.contains("hidden")) {
          hideMenu();
        } else if (state.gameStarted) {
          showMenu();
        }
      }
    });

    /* Focus input on click anywhere (only when game is active) */
    document.addEventListener("click", function (e) {
      if (state.gameStarted && titleScreen.classList.contains("hidden") &&
          !e.target.closest("#title-screen") && !e.target.closest(".menu-btn") &&
          !e.target.closest("#ingame-menu-btn")) {
        commandInput.focus();
      }
    });

    updateStatus();

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
      hasSave = typeof localStorage !== "undefined" && localStorage.getItem(SAVE_KEY) !== null;
    } catch (e) {
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

    /* Clear story output */
    storyOutput.innerHTML = "";

    hideMenu();
    updateStatus();
    loadSceneArt("darkness");

    /* Hook into interpreter if available */
    hookInterpreter();

    commandInput.focus();
  }

  function continueGame() {
    var saved;
    try {
      var raw = localStorage.getItem(SAVE_KEY);
      if (!raw) return;
      saved = JSON.parse(raw);
    } catch (e) {
      return;
    }

    /* Restore saved state */
    if (saved.o2 !== undefined) state.o2 = saved.o2;
    if (saved.morale !== undefined) state.morale = saved.morale;
    if (saved.inventory !== undefined) state.inventory = saved.inventory;
    if (saved.currentRoom !== undefined) state.currentRoom = saved.currentRoom;
    if (saved.commandHistory !== undefined) state.commandHistory = saved.commandHistory;
    state.historyIndex = state.commandHistory.length;
    state.gameStarted = true;

    /* Clear story output and show restored message */
    storyOutput.innerHTML = "";

    hideMenu();
    updateStatus();

    if (state.currentRoom) {
      loadSceneArt(state.currentRoom.toLowerCase());
    } else {
      loadSceneArt("darkness");
    }

    appendSystemText("[Game restored.]");
    hookInterpreter();

    commandInput.focus();
  }

  function saveGame() {
    try {
      var data = {
        o2: state.o2,
        morale: state.morale,
        inventory: state.inventory,
        currentRoom: state.currentRoom,
        commandHistory: state.commandHistory,
      };
      localStorage.setItem(SAVE_KEY, JSON.stringify(data));
    } catch (e) {
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
  function appendStoryText(text) {
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
    if (state.currentRoom === roomName) return;
    state.currentRoom = roomName;
    var key = roomName.toLowerCase();
    loadSceneArt(key);
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

    /* Wrap GlkOte.update to intercept output */
    var originalUpdate = window.GlkOte.update;
    window.GlkOte.update = (arg) => {
      if (arg?.content) {
        for (let i = 0; i < arg.content.length; i++) {
          const win = arg.content[i];
          if (win.text) {
            for (let j = 0; j < win.text.length; j++) {
              const line = win.text[j];
              if (line.content) {
                const fullText = extractGlkText(line.content);
                if (fullText.trim()) {
                  appendStoryText(fullText);
                }
              }
            }
          }
        }
      }
      return originalUpdate.call(window.GlkOte, arg);
    };

    appendSystemText("[Interpreter connected.]");
  }

  function hookParchment() {
    state.interpreterReady = true;
    appendSystemText("[Parchment interpreter connected.]");
  }

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
   */
  function sendToInterpreter(cmd) {
    if (state.interpreterReady && typeof window.GlkOte !== "undefined") {
      /* Feed input to GlkOte */
      if (window.GlkOte.accept) {
        window.GlkOte.accept({
          type: "line",
          gen: window.GlkOte.generation || 0,
          value: cmd,
        });
      }
      return;
    }

    /* Standalone shell mode — handle basic commands for demo */
    handleShellCommand(cmd);
  }

  /* ── Shell mode (no interpreter) ── */
  function handleShellCommand(cmd) {
    var lower = cmd.toLowerCase().trim();

    if (lower === "look" || lower === "l") {
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
        "Available commands: look, inventory, north, south, east, west, help\n\n[Shell mode — load a Glulx interpreter for the full game experience.]",
      );
    } else {
      appendStoryText(
        "I didn't understand that command. Type 'help' for available commands.",
      );
    }

    updateStatus();
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
      updateStatus();
    },
    showMenu: showMenu,
    hideMenu: hideMenu,
    saveGame: saveGame,
    startNewGame: startNewGame,
    continueGame: continueGame,
  };

  /* ── Boot ── */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
