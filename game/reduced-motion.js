/**
 * MIR'S END — Reduced-motion accessibility (#144).
 *
 * Three modes:
 *   "auto" — follow the OS `prefers-reduced-motion: reduce` media query
 *   "on"   — force reduced motion regardless of OS setting
 *   "off"  — force full motion regardless of OS setting
 *
 * When reduced motion resolves to true, `<html>` gains the `reduced-motion`
 * class. CSS rules under `html.reduced-motion` strip the cursor-blink
 * animation, button transitions, and similar motion. The scanline sweep
 * is driven from JS (initScanline in ui.js) and skips itself when
 * MirsEndMotion.isReduced() is true.
 *
 * Settings access:
 *   - The title-screen Settings button (#menu-settings) opens a small
 *     mode-cycle dialog
 *   - Mode persists in localStorage under MIRSEND_REDUCED_MOTION_KEY
 *
 * Wired pieces:
 *   - reduced-motion.js (this file): preference manager + Settings dialog
 *   - ui.css: @media (prefers-reduced-motion: reduce) + html.reduced-motion rules
 *   - ui.js initScanline(): gates on isReduced()
 */

(() => {
  var STORAGE_KEY = "mirsend_reduced_motion_mode";
  var VALID_MODES = ["auto", "on", "off"];

  var _mode = "auto";
  var _mediaQuery = null;
  var _reduced = false;

  function loadMode() {
    var raw;
    try {
      raw = localStorage.getItem(STORAGE_KEY);
    } catch (_e) {
      raw = null;
    }
    if (raw && VALID_MODES.indexOf(raw) !== -1) return raw;
    return "auto";
  }

  function saveMode(mode) {
    try {
      localStorage.setItem(STORAGE_KEY, mode);
    } catch (_e) {
      /* ignore */
    }
  }

  function resolve(mode) {
    if (mode === "on") return true;
    if (mode === "off") return false;
    return !!_mediaQuery?.matches;
  }

  function applyClass(reduced) {
    _reduced = reduced;
    var root = document.documentElement;
    if (reduced) root.classList.add("reduced-motion");
    else root.classList.remove("reduced-motion");
  }

  function setMode(mode) {
    if (VALID_MODES.indexOf(mode) === -1) return;
    _mode = mode;
    saveMode(mode);
    applyClass(resolve(mode));
  }

  function cycleMode() {
    var idx = VALID_MODES.indexOf(_mode);
    var next = VALID_MODES[(idx + 1) % VALID_MODES.length];
    setMode(next);
    return next;
  }

  /* ── Settings dialog ───────────────────────────────────────────────── */

  function modeLabel(mode) {
    if (mode === "auto") return "AUTO (follow OS)";
    if (mode === "on") return "ON (force reduced)";
    return "OFF (force full motion)";
  }

  function openSettings() {
    var existing = document.getElementById("settings-overlay");
    if (existing) existing.remove();

    var overlay = document.createElement("div");
    overlay.id = "settings-overlay";
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeSettings();
    });

    var modal = document.createElement("div");
    modal.id = "settings-modal";

    var title = document.createElement("h2");
    title.textContent = "Settings";
    modal.appendChild(title);

    var row = document.createElement("div");
    row.className = "settings-row";

    var label = document.createElement("span");
    label.className = "settings-label";
    label.textContent = "Reduced motion";
    row.appendChild(label);

    var value = document.createElement("button");
    value.className = "settings-value";
    value.id = "settings-reduced-motion";
    value.textContent = modeLabel(_mode);
    value.addEventListener("click", () => {
      cycleMode();
      value.textContent = modeLabel(_mode);
    });
    row.appendChild(value);

    modal.appendChild(row);

    var close = document.createElement("button");
    close.id = "settings-close";
    close.textContent = "Close";
    close.addEventListener("click", closeSettings);
    modal.appendChild(close);

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
  }

  function closeSettings() {
    var existing = document.getElementById("settings-overlay");
    if (existing) existing.remove();
  }

  function wireSettingsButton() {
    var btn = document.getElementById("menu-settings");
    if (!btn) return;
    btn.disabled = false;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      openSettings();
    });
  }

  /* ── Init ──────────────────────────────────────────────────────────── */

  function init() {
    if (typeof window.matchMedia === "function") {
      _mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      _mediaQuery.addEventListener("change", () => {
        if (_mode === "auto") applyClass(resolve("auto"));
      });
    }
    _mode = loadMode();
    applyClass(resolve(_mode));
    wireSettingsButton();
  }

  /* ── Public API ────────────────────────────────────────────────────── */

  window.MirsEndMotion = {
    init: init,
    getMode: () => _mode,
    setMode: setMode,
    cycleMode: cycleMode,
    isReduced: () => _reduced,
    openSettings: openSettings,
    closeSettings: closeSettings,
    MODES: VALID_MODES,
    STORAGE_KEY: STORAGE_KEY,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
