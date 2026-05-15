/**
 * MIR'S END — Soviet POST-style Boot Sequence
 * Displays a hardware POST/boot screen while Glulx initializes.
 */

(() => {
  /* ── POST lines — mix of Cyrillic and Latin ── */
  var BOOT_LINES = [
    "МИР-2 / MIR-2 STATION TERMINAL ИЭ-15 v3.4",
    "ROM CHECK ........................ OK",
    "MEMORY 64K ....................... OK",
    "LIFE SUPPORT INIT ................ OK",
    "ПИТ / PWR ........................ NOMINAL",
    "АРГОН-87 HANDSHAKE ............... ACK",
    "TELEMETRY SYNC 412KM ............. LOCK",
    "СВЯЗЬ / COMM ..................... DEGRADED",
  ];

  var READY_LINE = "READY / ГОТОВ";
  var LINE_INTERVAL = 200; /* ms between each line */
  var READY_PAUSE = 400; /* ms pause before READY line */
  var HOLD_AFTER_READY = 600; /* ms to hold READY before transition */

  var bootActive = false;
  var timers = [];
  var overlay;
  var textContainer;
  var skipEl;
  var onCompleteCallback = null;
  var bootStartTime = 0;

  /** Build boot DOM elements */
  function buildBootDOM() {
    overlay = document.createElement("div");
    overlay.id = "boot-overlay";

    textContainer = document.createElement("div");
    textContainer.id = "boot-text";
    overlay.appendChild(textContainer);

    skipEl = document.createElement("div");
    skipEl.id = "boot-skip";
    skipEl.textContent = "Press any key to skip";

    document.body.appendChild(overlay);
    document.body.appendChild(skipEl);
  }

  /** Show a single POST line */
  function showLine(text, extraClass) {
    var el = document.createElement("div");
    el.className = "boot-line" + (extraClass ? " " + extraClass : "");
    el.textContent = text;
    textContainer.appendChild(el);
    /* Force reflow then add visible class */
    el.offsetHeight; /* eslint-disable-line no-unused-expressions */
    el.classList.add("visible");
  }

  /** Cancel all pending timers */
  function cancelTimers() {
    for (var i = 0; i < timers.length; i++) {
      clearTimeout(timers[i]);
    }
    timers = [];
  }

  /** End the boot sequence and transition */
  function endBoot() {
    if (!bootActive) return;
    bootActive = false;
    cancelTimers();

    /* Clean up listeners */
    document.removeEventListener("keydown", handleSkip);
    document.removeEventListener("click", handleSkipClick);

    /* Fade out overlay */
    overlay.style.transition = "opacity 0.5s ease-out";
    overlay.style.opacity = "0";
    skipEl.style.transition = "opacity 0.2s ease-out";
    skipEl.style.opacity = "0";

    var timer = setTimeout(function () {
      overlay.classList.add("hidden");
      overlay.remove();
      skipEl.remove();

      if (onCompleteCallback) {
        onCompleteCallback();
      }
    }, 600);
    timers.push(timer);
  }

  /** Handle keypress to skip */
  function handleSkip(e) {
    if (!bootActive) return;
    e.preventDefault();
    endBoot();
  }

  /** Handle click to skip */
  function handleSkipClick(e) {
    if (!bootActive) return;
    /* Ignore clicks in the first 300ms to prevent accidental skip */
    if (Date.now() - bootStartTime < 300) return;
    e.preventDefault();
    endBoot();
  }

  /** Run the boot sequence */
  function runBoot() {
    bootActive = true;
    bootStartTime = Date.now();
    buildBootDOM();

    /* Hide the title screen during boot */
    var titleScreen = document.getElementById("title-screen");
    if (titleScreen) {
      titleScreen.style.display = "none";
    }

    /* Show skip hint after 800ms */
    var skipTimer = setTimeout(function () {
      if (bootActive) skipEl.classList.add("visible");
    }, 800);
    timers.push(skipTimer);

    /* Attach skip listeners */
    document.addEventListener("keydown", handleSkip);
    document.addEventListener("click", handleSkipClick);

    /* Schedule each POST line */
    for (var i = 0; i < BOOT_LINES.length; i++) {
      (function (index) {
        var timer = setTimeout(function () {
          if (!bootActive) return;
          showLine(BOOT_LINES[index]);
        }, index * LINE_INTERVAL);
        timers.push(timer);
      })(i);
    }

    /* Schedule READY line after all POST lines + pause */
    var readyDelay = BOOT_LINES.length * LINE_INTERVAL + READY_PAUSE;
    var readyTimer = setTimeout(function () {
      if (!bootActive) return;
      showLine(READY_LINE, "boot-ready");

      /* Add blinking cursor */
      var cursor = document.createElement("span");
      cursor.id = "boot-cursor";
      var readyEl = textContainer.querySelector(".boot-ready");
      if (readyEl) readyEl.appendChild(cursor);
    }, readyDelay);
    timers.push(readyTimer);

    /* End boot after READY holds */
    var endDelay = readyDelay + HOLD_AFTER_READY;
    var endTimer = setTimeout(function () {
      if (!bootActive) return;
      endBoot();
    }, endDelay);
    timers.push(endTimer);
  }

  /* ── Public API ── */
  window.MirsEndBoot_POST = {
    run: function (callback) {
      onCompleteCallback = callback || null;
      runBoot();
    },
    skip: endBoot,
    isActive: function () {
      return bootActive;
    },
    LINES: BOOT_LINES,
    READY_LINE: READY_LINE,
    LINE_INTERVAL: LINE_INTERVAL,
  };
})();
