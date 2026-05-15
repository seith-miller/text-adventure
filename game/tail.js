/**
 * MIR'S END — live playthrough tail.
 *
 * Streams every player input and story-output span to a local tail server
 * (127.0.0.1:8788) so a side-by-side reviewer / coach can watch the game
 * unfold in real time. Fire-and-forget; if the tail server isn't running
 * the game continues normally — `.catch(() => {})` swallows the failure.
 *
 * Only fires when the page is served from localhost / 127.0.0.1, so a
 * production deploy never tries to POST anywhere.
 */

(() => {
  const isLocal =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";
  if (!isLocal) return;

  const URL = "http://127.0.0.1:8788/tail";

  function send(obj) {
    try {
      fetch(URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(obj),
        keepalive: true,
      }).catch(() => {});
    } catch (_e) {
      /* ignore */
    }
  }

  function hook() {
    const out = document.getElementById("story-output");
    if (!out) {
      // ui.js init hasn't run yet — try again next tick.
      setTimeout(hook, 50);
      return;
    }

    // Snapshot anything already in #story-output (handles late-load /
    // continue-game cases where the transcript already has turns in it).
    if (out.textContent.trim()) {
      send({ kind: "snapshot", text: out.textContent });
    }

    const obs = new MutationObserver((muts) => {
      for (const m of muts) {
        for (const node of m.addedNodes) {
          const text = (node.textContent || "").trimEnd();
          const cls = node.className || node.nodeName || "text";
          if (text) send({ kind: cls, text });
        }
      }
    });
    obs.observe(out, { childList: true });

    console.log("[mirsend-tail] live → 127.0.0.1:8788/tail");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", hook);
  } else {
    hook();
  }
})();
