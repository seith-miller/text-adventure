/**
 * MIR'S END — Intro Sequence
 * Atmospheric timed-text introduction that plays before the game begins.
 */

(() => {
  /* ── Intro sequence steps ── */
  var INTRO_STEPS = [
    { text: "CLASSIFIED // EYES ONLY", style: "intro-datestamp", delay: 0 },
    {
      text: "17 MARCH 1988  //  02:14 MSK",
      style: "intro-datestamp",
      delay: 1500,
    },
    {
      text: "LOW EARTH ORBIT  //  ALT 350 KM",
      style: "intro-location",
      delay: 3500,
    },
    {
      text: "SOVIET ORBITAL STATION MIR-2",
      style: "intro-location",
      delay: 5500,
    },
    { clear: true, delay: 8000 },
    {
      text: "The station drifts in silence above the nightside.",
      style: "intro-narrative",
      delay: 9000,
    },
    {
      text: "Below, city lights trace coastlines like circuits on a board.",
      style: "intro-narrative",
      delay: 11500,
    },
    {
      text: "Inside, the crew sleeps. Instruments hum. All systems nominal.",
      style: "intro-narrative",
      delay: 14000,
    },
    { clear: true, delay: 17500 },
    { text: "Then\u2014", style: "intro-emphasis", delay: 18500 },
    { flash: true, delay: 19500 },
    { clear: true, delay: 20000 },
    {
      text: "Every screen goes white.",
      style: "intro-narrative",
      delay: 22000,
    },
    { text: "Then black.", style: "intro-emphasis", delay: 24000 },
    { clear: true, delay: 26500 },
    { text: ". . .", style: "intro-silence", delay: 28000 },
    { clear: true, delay: 31000 },
    { text: "MIR\u2019S END", style: "intro-title", delay: 32500 },
    {
      text: "An Interactive Survival Story",
      style: "intro-subtitle",
      delay: 34500,
    },
    { end: true, delay: 38000 },
  ];

  var STORAGE_KEY = "mirsend_intro_seen";
  var introActive = false;
  var timers = [];
  var overlay;
  var textContainer;
  var flashEl;
  var skipEl;
  var staticEl;
  var onCompleteCallback = null;

  /**
   * Check whether intro should play.
   * Returns false if:
   *  - Previously completed (sessionStorage)
   *  - URL has ?skip_intro or #skip_intro
   *  - Game is being loaded/continued
   */
  function shouldPlayIntro() {
    /* Check sessionStorage — intro already seen this session */
    try {
      if (sessionStorage.getItem(STORAGE_KEY)) return false;
    } catch (_e) {
      /* sessionStorage unavailable — proceed */
    }

    /* Check URL params */
    var search = window.location.search || "";
    var hash = window.location.hash || "";
    if (
      search.indexOf("skip_intro") !== -1 ||
      hash.indexOf("skip_intro") !== -1
    ) {
      return false;
    }

    /* Check for continue/load markers */
    if (search.indexOf("continue") !== -1 || search.indexOf("load") !== -1) {
      return false;
    }

    return true;
  }

  /** Build intro DOM elements */
  function buildIntroDOM() {
    overlay = document.createElement("div");
    overlay.id = "intro-overlay";

    textContainer = document.createElement("div");
    textContainer.id = "intro-text";
    overlay.appendChild(textContainer);

    flashEl = document.createElement("div");
    flashEl.id = "intro-flash";

    staticEl = document.createElement("div");
    staticEl.id = "intro-static";

    skipEl = document.createElement("div");
    skipEl.id = "intro-skip";
    skipEl.textContent = "Press any key to skip";

    document.body.appendChild(overlay);
    document.body.appendChild(flashEl);
    document.body.appendChild(staticEl);
    document.body.appendChild(skipEl);
  }

  /** Check if reduced motion is active */
  function isReducedMotion() {
    return document.documentElement.classList.contains("reduced-motion");
  }

  /** Clear all visible intro lines with fade-out (or hard cut) */
  function clearText() {
    var lines = textContainer.querySelectorAll(".intro-line");
    for (let i = 0; i < lines.length; i++) {
      lines[i].classList.add("fade-out");
      lines[i].classList.remove("visible");
    }
    /* Remove faded lines after transition (instant in reduced-motion) */
    var removeDelay = isReducedMotion() ? 0 : 900;
    var timer = setTimeout(() => {
      textContainer.innerHTML = "";
    }, removeDelay);
    timers.push(timer);
  }

  /** Show a single intro line */
  function showLine(text, style) {
    var el = document.createElement("div");
    el.className = `intro-line ${style}`;
    el.textContent = text;
    textContainer.appendChild(el);
    /* Force reflow then add visible class */
    el.offsetHeight; /* eslint-disable-line no-unused-expressions */
    el.classList.add("visible");
  }

  /** Trigger the EMP flash effect */
  function triggerFlash() {
    flashEl.classList.add("flash");
    staticEl.classList.add("active");
    var timer = setTimeout(() => {
      staticEl.classList.remove("active");
    }, 2500);
    timers.push(timer);
  }

  /** Cancel all pending timers */
  function cancelTimers() {
    for (let i = 0; i < timers.length; i++) {
      clearTimeout(timers[i]);
    }
    timers = [];
  }

  /** End the intro and transition to the game */
  function endIntro() {
    if (!introActive) return;
    introActive = false;
    cancelTimers();

    /* Mark intro as seen */
    try {
      sessionStorage.setItem(STORAGE_KEY, "1");
    } catch (_e) {
      /* ignore */
    }

    /* Clean up skip listener */
    document.removeEventListener("keydown", handleSkip);
    document.removeEventListener("click", handleSkipClick);

    /* Fade out overlay (hard cut when reduced motion) */
    var fadeDelay = isReducedMotion() ? 0 : 1300;
    if (!isReducedMotion()) {
      overlay.style.transition = "opacity 1.2s ease-out";
      skipEl.style.transition = "opacity 0.3s ease-out";
    }
    overlay.style.opacity = "0";
    skipEl.style.opacity = "0";
    flashEl.style.display = "none";
    staticEl.style.display = "none";

    var timer = setTimeout(() => {
      overlay.classList.add("hidden");
      overlay.remove();
      flashEl.remove();
      staticEl.remove();
      skipEl.remove();

      /* Show the game shell */
      var gameShell = document.getElementById("game-shell");
      if (gameShell) {
        gameShell.style.display = "";
      }

      if (onCompleteCallback) {
        onCompleteCallback();
      }
    }, fadeDelay);
    timers.push(timer);
  }

  /** Handle keypress to skip */
  function handleSkip(e) {
    if (!introActive) return;
    e.preventDefault();
    endIntro();
  }

  /** Handle click to skip */
  function handleSkipClick(e) {
    if (!introActive) return;
    /* Ignore clicks in the first second to prevent accidental skip */
    if (Date.now() - introStartTime < 1000) return;
    e.preventDefault();
    endIntro();
  }

  var introStartTime = 0;

  /** Run the intro sequence */
  function runIntro() {
    introActive = true;
    introStartTime = Date.now();
    buildIntroDOM();

    /* Hide game shell during intro */
    var gameShell = document.getElementById("game-shell");
    if (gameShell) {
      gameShell.style.display = "none";
    }

    /* Show skip hint after 2 seconds */
    var skipTimer = setTimeout(() => {
      skipEl.classList.add("visible");
    }, 2000);
    timers.push(skipTimer);

    /* Attach skip listeners */
    document.addEventListener("keydown", handleSkip);
    document.addEventListener("click", handleSkipClick);

    /* Schedule each step */
    for (let i = 0; i < INTRO_STEPS.length; i++) {
      ((step) => {
        var timer = setTimeout(() => {
          if (!introActive) return;

          if (step.clear) {
            clearText();
          } else if (step.flash) {
            triggerFlash();
          } else if (step.end) {
            endIntro();
          } else if (step.text) {
            showLine(step.text, step.style || "intro-narrative");
          }
        }, step.delay);
        timers.push(timer);
      })(INTRO_STEPS[i]);
    }
  }

  /* ── Public API ── */
  window.MirsEndIntro = {
    shouldPlayIntro: shouldPlayIntro,
    run: (callback) => {
      onCompleteCallback = callback || null;
      if (shouldPlayIntro()) {
        runIntro();
      } else {
        if (onCompleteCallback) onCompleteCallback();
      }
    },
    skip: endIntro,
    isActive: () => introActive,
    STEPS: INTRO_STEPS,
    STORAGE_KEY: STORAGE_KEY,
  };
})();
