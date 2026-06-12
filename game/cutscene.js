/**
 * MIR'S END — Cutscene Transitions (#138)
 *
 * Per-column wipe transitions fired on module/room change. Mirrors the
 * corridor/airlock spatial transitions in the fiction — the player's
 * primary "scene change" feedback.
 *
 * Public API:
 *   MirsEndCutscene.transitionTo(sceneId, opts?)
 *       Trigger the wipe. opts.onComplete fires when the cutscene ends
 *       (or is skipped). If sceneId isn't registered, falls back to a
 *       plain wipe with no video body.
 *
 *   MirsEndCutscene.registerScene(sceneId, framesFile)
 *       Add (sceneId → frames file) to the registry at runtime.
 *
 *   MirsEndCutscene.skip()
 *       End any active cutscene immediately.
 *
 *   MirsEndCutscene.isActive() → boolean
 *
 *   MirsEndCutscene.REGISTRY → the current registry object
 *
 * The wipe is rendered as an absolutely-positioned <pre> overlay above
 * the terminal screen so it never destroys the live display content or
 * the command-input element — game state and input are preserved.
 *
 * Reduced-motion (#144): when `(prefers-reduced-motion: reduce)` matches,
 * `transitionTo` becomes a hard cut: the onComplete callback fires on the
 * next tick with no animation or overlay.
 */

(() => {
  /* ── Grid constants — must match ui.js so the overlay is column-aligned ── */
  const TOTAL_W = 80;
  const TOTAL_H = 25;

  /* ── Timing knobs ── */
  const WIPE_DURATION = 1200; // total per-column wipe time, ms
  const VIDEO_HOLD_MS = 2200; // ms the video body holds before wiping back out

  /* ── Scene registry: sceneId → frames file path ──
     The frames file is expected to expose window.FRAMES (string[]) and
     optionally window.META = { fps }, like game/mockups/frames/space.js.
     The "frames/" prefix is resolved relative to the page (i.e., game/). */
  const REGISTRY = {
    // Default seeded entries — the issue calls out e.g. `corridor → frames/corridor.js`.
    // Files don't need to exist yet; missing files fall back to a plain wipe.
    "main corridor": "frames/corridor.js",
    corridor: "frames/corridor.js",
    "command module": "frames/command.js",
    "observation cupola": "frames/cupola.js",
    "crew quarters": "frames/crew.js",
    darkness: "frames/darkness.js",
  };

  /* ── State ── */
  let active = false;
  let overlay = null;
  let rafHandle = null;
  let skipListener = null;
  const loadedFrames = {}; // sceneId → string[] (cached after load)
  let currentOnComplete = null;

  /* ── Reduced-motion check ──
     Re-evaluated each call so user preference changes mid-session are picked up. */
  function reducedMotionPreferred() {
    try {
      return (
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
      );
    } catch (_e) {
      return false;
    }
  }

  /* ── Overlay management ──
     Mount an absolutely-positioned <pre> over the terminal screen. We never
     touch the live `#display` element so the game's screen state survives
     the cutscene unchanged. */
  function mountOverlay() {
    const screen = document.getElementById("screen");
    if (!screen) return null;

    const pre = document.createElement("pre");
    pre.id = "cutscene-overlay";
    /* Inline styles so the module doesn't need a separate CSS file. */
    pre.style.position = "absolute";
    pre.style.inset = "0";
    pre.style.margin = "0";
    pre.style.padding = "0";
    pre.style.display = "flex";
    pre.style.alignItems = "center";
    pre.style.justifyContent = "center";
    pre.style.whiteSpace = "pre";
    pre.style.fontFamily =
      "'IBM Plex Mono', 'Cascadia Mono', 'DejaVu Sans Mono', 'Consolas', 'Courier New', monospace";
    pre.style.fontFeatureSettings = '"liga" 0, "calt" 0';
    pre.style.color = "var(--phosphor, #6cf06b)";
    pre.style.background = "transparent";
    pre.style.pointerEvents = "none";
    pre.style.zIndex = "7"; // above scanlines (z=6) but below input overlays
    pre.style.fontSize = "16px";
    pre.style.lineHeight = "1.25";

    /* Reuse the live display's font-size so columns align visually. */
    const liveDisplay = document.getElementById("display");
    if (liveDisplay) {
      const computed = window.getComputedStyle(liveDisplay);
      if (computed.fontSize) pre.style.fontSize = computed.fontSize;
    }

    screen.appendChild(pre);
    return pre;
  }

  function unmountOverlay() {
    if (overlay?.parentNode) {
      overlay.parentNode.removeChild(overlay);
    }
    overlay = null;
  }

  /* ── Wipe column scheduling ── */
  const colDelay = new Float32Array(TOTAL_W);
  const colDur = new Float32Array(TOTAL_W);
  function rollWipeSchedule() {
    for (let x = 0; x < TOTAL_W; x++) {
      colDelay[x] = Math.random() * (WIPE_DURATION * 0.55);
      colDur[x] = WIPE_DURATION * 0.35 + Math.random() * (WIPE_DURATION * 0.25);
    }
  }

  /* ── Snapshot the live screen as plain text so we can wipe FROM it ── */
  function snapshotLiveScreen() {
    const display = document.getElementById("display");
    if (!display) return "";
    const text = display.textContent || "";
    /* Pad each row to TOTAL_W so per-column slicing is well-defined. */
    const rows = text.split("\n");
    for (let i = 0; i < rows.length; i++) {
      if (rows[i].length < TOTAL_W) {
        rows[i] = rows[i] + " ".repeat(TOTAL_W - rows[i].length);
      }
    }
    while (rows.length < TOTAL_H) rows.push(" ".repeat(TOTAL_W));
    return rows.join("\n");
  }

  /* ── Strip inline tags from a frame string ──
     (Frame files use <bri>/<dim>/etc.; for wipe slicing we want raw chars.) */
  function stripTags(s) {
    return (s || "").replace(/<[^>]+>/g, "").replace(/&[a-zA-Z0-9#]+;/g, "X");
  }

  /* ── Render one wipe frame ──
     fromPlain / toPlain are tag-stripped strings (TOTAL_W chars × TOTAL_H rows).
     If toPlain is empty (fallback / plain wipe — no video), the wipe reveals
     a grid of spaces instead of frame content. */
  function renderWipe(elapsed, fromPlain, toPlain) {
    if (!overlay) return;
    const fromRows = fromPlain.split("\n");
    const toRows = (toPlain || "").split("\n");
    const out = [];
    for (let y = 0; y < TOTAL_H; y++) {
      let row = "";
      for (let x = 0; x < TOTAL_W; x++) {
        const t = (elapsed - colDelay[x]) / colDur[x];
        const head = Math.floor(t * TOTAL_H);
        let ch;
        if (y <= head) {
          ch = toRows[y]?.[x] || " ";
        } else {
          ch = fromRows[y]?.[x] || " ";
        }
        row += ch;
      }
      out.push(row);
    }
    overlay.textContent = out.join("\n");
  }

  /* ── Frames loader ──
     Loads `frames/<scene>.js` via a <script> tag. Calls `done` with the
     FRAMES array, or with null on any failure (missing file, parse error,
     etc). Cached on success so subsequent transitions are instantaneous. */
  function loadFramesForScene(sceneId, done) {
    if (!sceneId) {
      done(null);
      return;
    }
    if (loadedFrames[sceneId]) {
      done(loadedFrames[sceneId]);
      return;
    }

    const path = REGISTRY[sceneId] || REGISTRY[String(sceneId).toLowerCase()];
    if (!path) {
      done(null);
      return;
    }

    const s = document.createElement("script");
    s.src = path;
    s.onload = () => {
      /* The frames files set window.FRAMES; capture and clear so the next
         load doesn't see stale data from a different scene. */
      const f = window.FRAMES || null;
      window.FRAMES = undefined;
      if (Array.isArray(f) && f.length) {
        loadedFrames[sceneId] = f;
        done(f);
      } else {
        done(null);
      }
    };
    s.onerror = () => {
      done(null);
    };
    document.head.appendChild(s);
  }

  /* ── Skip handler ──
     ANY keydown ends the cutscene. The listener is removed when the
     cutscene finishes so subsequent keystrokes go to the game. */
  function installSkipListener() {
    skipListener = (_e) => {
      skip();
    };
    document.addEventListener("keydown", skipListener, true);
  }
  function removeSkipListener() {
    if (skipListener) {
      document.removeEventListener("keydown", skipListener, true);
      skipListener = null;
    }
  }

  /* ── Lifecycle ── */
  function finish() {
    if (!active) return;
    active = false;
    if (rafHandle) {
      cancelAnimationFrame(rafHandle);
      rafHandle = null;
    }
    removeSkipListener();
    unmountOverlay();
    const cb = currentOnComplete;
    currentOnComplete = null;
    if (typeof cb === "function") {
      try {
        cb();
      } catch (_e) {
        /* swallow — onComplete failures must not break the game */
      }
    }
  }

  function skip() {
    if (!active) return;
    finish();
  }

  /* ── Main entry point ── */
  function transitionTo(sceneId, opts) {
    const options = opts || {};
    const onComplete =
      typeof options.onComplete === "function" ? options.onComplete : null;

    /* Reduced-motion path: hard cut. No overlay, no animation. The callback
       fires on the next tick so callers can rely on async ordering. */
    if (reducedMotionPreferred()) {
      if (onComplete) {
        setTimeout(onComplete, 0);
      }
      return;
    }

    /* If a cutscene is already running, end it first so we don't stack. */
    if (active) {
      finish();
    }

    currentOnComplete = onComplete;

    overlay = mountOverlay();
    if (!overlay) {
      /* No screen element — nothing to render onto. Fire callback. */
      if (onComplete) setTimeout(onComplete, 0);
      return;
    }

    active = true;
    installSkipListener();

    const fromPlain = snapshotLiveScreen();

    loadFramesForScene(sceneId, (frames) => {
      /* Missing or empty frames → fallback: plain wipe with no video body. */
      const hasFrames = Array.isArray(frames) && frames.length > 0;
      const videoFps = window.META?.fps || 12;
      window.META = undefined;

      const STATE = { WIPE_IN: 1, VIDEO: 2, WIPE_OUT: 3, FALLBACK_WIPE: 4 };
      let state = hasFrames ? STATE.WIPE_IN : STATE.FALLBACK_WIPE;
      let stateStart = 0;
      let videoFrameIdx = 0;
      let videoLastTick = 0;

      rollWipeSchedule();

      const tickVideo = (now) => {
        if (!hasFrames) return;
        if (now - videoLastTick >= 1000 / videoFps) {
          videoFrameIdx = (videoFrameIdx + 1) % frames.length;
          videoLastTick = now;
        }
      };

      const loop = (now) => {
        if (!active) return;
        if (!stateStart) stateStart = now;
        const elapsed = now - stateStart;
        tickVideo(now);

        if (state === STATE.WIPE_IN) {
          const toPlain = stripTags(frames[videoFrameIdx]);
          renderWipe(elapsed, fromPlain, toPlain);
          if (elapsed >= WIPE_DURATION) {
            state = STATE.VIDEO;
            stateStart = now;
          }
        } else if (state === STATE.VIDEO) {
          /* Show the raw tagged frame using innerHTML for color. */
          overlay.innerHTML = frames[videoFrameIdx];
          if (elapsed >= VIDEO_HOLD_MS) {
            state = STATE.WIPE_OUT;
            stateStart = now;
            rollWipeSchedule();
          }
        } else if (state === STATE.WIPE_OUT) {
          const fromVideo = stripTags(frames[videoFrameIdx]);
          renderWipe(elapsed, fromVideo, snapshotLiveScreen());
          if (elapsed >= WIPE_DURATION) {
            finish();
            return;
          }
        } else if (state === STATE.FALLBACK_WIPE) {
          /* No frames registered — plain wipe over the live screen. */
          const blank = " ".repeat(TOTAL_W);
          const blankScreen = new Array(TOTAL_H).fill(blank).join("\n");
          renderWipe(elapsed, fromPlain, blankScreen);
          if (elapsed >= WIPE_DURATION) {
            renderWipe(WIPE_DURATION, blankScreen, snapshotLiveScreen());
            finish();
            return;
          }
        }
        rafHandle = requestAnimationFrame(loop);
      };
      rafHandle = requestAnimationFrame(loop);
    });
  }

  function registerScene(sceneId, framesFile) {
    if (!sceneId || !framesFile) return;
    REGISTRY[sceneId] = framesFile;
    /* Invalidate cache so the new file is loaded on next transition. */
    delete loadedFrames[sceneId];
  }

  /* ── Public API ── */
  window.MirsEndCutscene = {
    transitionTo: transitionTo,
    registerScene: registerScene,
    skip: skip,
    isActive: () => active,
    REGISTRY: REGISTRY,
  };
})();
