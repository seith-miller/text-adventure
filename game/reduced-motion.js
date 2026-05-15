/**
 * MIR'S END — Reduced-Motion Accessibility Manager
 *
 * Respects prefers-reduced-motion: reduce and provides an in-game toggle.
 * Modes: "auto" (follow OS), "on" (always reduce), "off" (never reduce).
 *
 * When active, adds class "reduced-motion" to <html>, which CSS uses to
 * gate animations (scanline sweep, cursor blink, intro fades, etc.).
 */

(() => {
  var STORAGE_KEY = "mirsend_reduced_motion";
  var VALID_MODES = ["auto", "on", "off"];

  /* Current effective state: true = reduce motion */
  var _reducedMotion = false;
  /* User-chosen mode */
  var _mode = "auto";
  /* OS-level media query */
  var _mql = null;

  /** Read persisted preference, default to "auto". */
  function loadMode() {
    var stored;
    try {
      stored = localStorage.getItem(STORAGE_KEY);
      if (stored && VALID_MODES.indexOf(stored) !== -1) {
        return stored;
      }
    } catch (_e) {
      /* localStorage unavailable */
    }
    return "auto";
  }

  /** Persist the user's chosen mode. */
  function saveMode(mode) {
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch (_e) {
      /* ignore */
    }
  }

  /** Resolve effective reduced-motion state from mode + OS pref. */
  function resolve() {
    if (_mode === "on") return true;
    if (_mode === "off") return false;
    /* auto — follow OS */
    return _mql ? _mql.matches : false;
  }

  /** Apply the current state to the DOM. */
  function apply() {
    _reducedMotion = resolve();
    var root = document.documentElement;
    if (_reducedMotion) {
      root.classList.add("reduced-motion");
    } else {
      root.classList.remove("reduced-motion");
    }
  }

  /** Set mode and apply. */
  function setMode(mode) {
    if (VALID_MODES.indexOf(mode) === -1) return;
    _mode = mode;
    saveMode(mode);
    apply();
  }

  /** Cycle through modes: auto -> on -> off -> auto */
  function cycleMode() {
    var idx = VALID_MODES.indexOf(_mode);
    var next = VALID_MODES[(idx + 1) % VALID_MODES.length];
    setMode(next);
    return next;
  }

  /** Initialize — call as early as possible. */
  function init() {
    _mode = loadMode();

    /* Set up OS-level media query listener */
    if (window.matchMedia) {
      _mql = window.matchMedia("(prefers-reduced-motion: reduce)");
      _mql.addEventListener("change", () => {
        if (_mode === "auto") apply();
      });
    }

    apply();
  }

  /* ── Public API ── */
  window.MirsEndMotion = {
    init: init,
    getMode: () => _mode,
    setMode: setMode,
    cycleMode: cycleMode,
    isReduced: () => _reducedMotion,
    MODES: VALID_MODES,
  };

  /* Auto-init on load so the class is applied before first paint. */
  init();
})();
