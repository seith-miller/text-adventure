/**
 * MIR'S END — Reduced-Motion Accessibility Module
 *
 * Detects OS-level prefers-reduced-motion and provides an in-game
 * settings toggle (off / on / auto). When active, adds .reduced-motion
 * to <html> so CSS can gate all animations.
 */

(() => {
  var STORAGE_KEY = "mirsend_reduced_motion";
  var VALID_MODES = ["auto", "on", "off"];
  var _mode = "auto";
  var _reducedMotion = false;
  var _mediaQuery = null;

  /** Read persisted mode from localStorage, default to "auto". */
  function loadMode() {
    try {
      var stored = localStorage.getItem(STORAGE_KEY);
      if (stored && VALID_MODES.indexOf(stored) !== -1) {
        return stored;
      }
    } catch (_e) {
      /* localStorage unavailable */
    }
    return "auto";
  }

  /** Persist the current mode to localStorage. */
  function saveMode(mode) {
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch (_e) {
      /* localStorage unavailable */
    }
  }

  /** Resolve whether reduced motion should be active. */
  function resolve(mode) {
    if (mode === "on") return true;
    if (mode === "off") return false;
    /* "auto" — follow OS preference */
    return _mediaQuery ? _mediaQuery.matches : false;
  }

  /** Apply the .reduced-motion class to <html>. */
  function apply(reduced) {
    _reducedMotion = reduced;
    var root = document.documentElement;
    if (reduced) {
      root.classList.add("reduced-motion");
    } else {
      root.classList.remove("reduced-motion");
    }
  }

  /** Set a new mode and persist it. */
  function setMode(mode) {
    if (VALID_MODES.indexOf(mode) === -1) return;
    _mode = mode;
    saveMode(mode);
    apply(resolve(mode));
  }

  /** Cycle through modes: auto → on → off → auto. */
  function cycleMode() {
    var idx = VALID_MODES.indexOf(_mode);
    var next = VALID_MODES[(idx + 1) % VALID_MODES.length];
    setMode(next);
    return next;
  }

  /** Initialize: load preference, detect OS setting, apply. */
  function init() {
    /* Set up media query listener */
    if (typeof window.matchMedia === "function") {
      _mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      _mediaQuery.addEventListener("change", () => {
        if (_mode === "auto") {
          apply(resolve("auto"));
        }
      });
    }

    _mode = loadMode();
    apply(resolve(_mode));
  }

  /* ── Public API ── */
  window.MirsEndMotion = {
    init: init,
    getMode: function () { return _mode; },
    setMode: setMode,
    cycleMode: cycleMode,
    isReduced: function () { return _reducedMotion; },
    MODES: VALID_MODES,
    STORAGE_KEY: STORAGE_KEY,
  };
})();
