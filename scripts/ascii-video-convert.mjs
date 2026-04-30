#!/usr/bin/env node
/*
  ascii-video-convert.mjs

  Convert a video file (anything ffmpeg can read) into a JS module
  of pre-rendered ASCII frames, ready to feed to AsciiPlayer.

  Pipeline:
    ffmpeg → raw grayscale @ width × (height*2) @ fps  (piped to stdout)
    → average each pair of vertical pixels into one char cell
    → map brightness 0..255 to a ramp glyph
    → emit a JS file with FRAMES (string[]) and META

  Why height*2: terminal cells are roughly 2× taller than wide, so
  to keep the source video's aspect ratio, we sample at 2× vertical
  resolution then average pairs of rows into one char. This avoids
  a vertically squished image on screen.

  Requirements:
    - Node 18+
    - ffmpeg on PATH  (macOS: `brew install ffmpeg`)

  Usage:
    node scripts/ascii-video-convert.mjs <input> <output.js> [options]

  Options:
    --width=76          char grid width             (default 76)
    --height=19         char grid height            (default 19)
    --fps=12            playback fps                (default 12)
    --invert            invert brightness (use for white-on-black sources
                        where you want bright pixels = sparse glyph)
    --ramp="..."        custom char ramp, dark→light
                        (default ' .:;-=+*#%@')
    --tiers=3           brightness tiers: 1 = single color, 3 = dim/normal/
                        bright wrapped in <dim>/<bri> tags using the page's
                        existing CSS color classes. Default 1.
    --name=FRAMES       exported variable name      (default FRAMES)
    --start=00:00:00    start timestamp (passed to ffmpeg -ss)
    --duration=5        length in seconds (passed to ffmpeg -t)

  Example:
    node scripts/ascii-video-convert.mjs distress.mp4 \
      game/mockups/frames/distress.js \
      --width=76 --height=19 --fps=12 --duration=8
*/

import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";

// ── Argument parsing ─────────────────────────────────────────
function parseArgs(argv) {
  const positional = [];
  const opts = {
    width: 76,
    height: 19,
    fps: 12,
    invert: false,
    ramp: " .:;-=+*#%@",
    tiers: 1,
    name: "FRAMES",
    start: null,
    duration: null,
  };
  for (const a of argv) {
    if (a.startsWith("--")) {
      const [k, v] = a.slice(2).split("=");
      if (v === undefined) opts[k] = true;
      else if (k === "width" || k === "height" || k === "fps" || k === "tiers")
        opts[k] = parseInt(v, 10);
      else if (k === "duration") opts[k] = parseFloat(v);
      else opts[k] = v;
    } else {
      positional.push(a);
    }
  }
  opts.input = positional[0];
  opts.output = positional[1];
  return opts;
}

// ── ffmpeg invocation ────────────────────────────────────────
function runFfmpeg(args) {
  return new Promise((resolve, reject) => {
    const ff = spawn("ffmpeg", args);
    const chunks = [];
    let stderr = "";
    ff.stdout.on("data", (d) => chunks.push(d));
    ff.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    ff.on("error", (e) => {
      if (e.code === "ENOENT") {
        reject(
          new Error(
            "ffmpeg not found on PATH. Install with `brew install ffmpeg`.",
          ),
        );
      } else {
        reject(e);
      }
    });
    ff.on("close", (code) => {
      if (code !== 0) reject(new Error(`ffmpeg exited ${code}\n${stderr}`));
      else resolve(Buffer.concat(chunks));
    });
  });
}

// ── Brightness → glyph for one frame ─────────────────────────
//
// When tiers > 1, we wrap runs of glyphs in <dim>/<bri> tags so the
// page's existing CSS classes paint multiple phosphor brightness
// levels. tiers=3 splits the ramp into [dim, normal, bri].
function frameToAscii(buf, offset, width, height, ramp, invert, tiers) {
  const rampLen = ramp.length;
  // Map ramp index → tier name (or null for 'normal', no tag)
  const TIER_NAMES = {
    1: () => null,
    3: (idx) => {
      const band = Math.floor((idx * 3) / rampLen); // 0=dim 1=normal 2=bright
      return band === 0 ? "dim" : band === 2 ? "bri" : null;
    },
  };
  const tierName = TIER_NAMES[tiers] || TIER_NAMES[1];

  const rows = [];
  for (let y = 0; y < height; y++) {
    let row = "";
    let openTag = null;
    for (let x = 0; x < width; x++) {
      // Average two vertical pixels (one char cell = 1 wide × 2 tall)
      const a = buf[offset + y * 2 * width + x];
      const b = buf[offset + (y * 2 + 1) * width + x];
      let g = (a + b) / 2 / 255;
      if (invert) g = 1 - g;
      const idx = Math.max(
        0,
        Math.min(rampLen - 1, Math.floor(g * (rampLen - 1) + 0.0001)),
      );
      const t = tierName(idx);
      if (t !== openTag) {
        if (openTag) row += `</${openTag}>`;
        if (t) row += `<${t}>`;
        openTag = t;
      }
      row += ramp[idx];
    }
    if (openTag) row += `</${openTag}>`;
    rows.push(row);
  }
  return rows.join("\n");
}

// ── Emit the JS module ───────────────────────────────────────
function emitModule({ output, name, frames, meta }) {
  const banner = `// Auto-generated by scripts/ascii-video-convert.mjs
// Source: ${meta.input}
// Meta:   ${JSON.stringify({ width: meta.width, height: meta.height, fps: meta.fps, count: frames.length })}
// Do not edit by hand.
`;
  // Frames are JSON-stringified for safe escaping. The result is a single
  // big array literal; modern JS engines parse this in tens of ms even
  // for thousands of frames.
  // IIFE-wrapped so the const declarations don't collide with other
  // classic scripts on the page (browsers share global lexical scope
  // across non-module scripts). Also exports for Node CJS consumers.
  const body = `(function (root) {
  const META = ${JSON.stringify({ width: meta.width, height: meta.height, fps: meta.fps, count: frames.length, ramp: meta.ramp })};
  const ${name} = [
${frames.map((f) => `    ${JSON.stringify(f)}`).join(",\n")}
  ];
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { META, ${name} };
  } else if (root) {
    root.META = META;
    root.${name} = ${name};
  }
})(typeof window !== 'undefined' ? window : null);
`;
  writeFileSync(output, banner + body);
}

// ── Main ─────────────────────────────────────────────────────
async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (!opts.input || !opts.output) {
    console.error(
      "Usage: node scripts/ascii-video-convert.mjs <input> <output.js> [options]",
    );
    console.error("See file header for options.");
    process.exit(1);
  }

  const {
    input,
    output,
    width,
    height,
    fps,
    invert,
    ramp,
    name,
    start,
    duration,
    tiers,
  } = opts;
  const srcH = height * 2;

  const ffArgs = ["-hide_banner", "-loglevel", "error"];
  if (start) ffArgs.push("-ss", start);
  if (duration) ffArgs.push("-t", String(duration));
  ffArgs.push(
    "-i",
    input,
    "-vf",
    `fps=${fps},` +
      `scale=${width}:${srcH}:force_original_aspect_ratio=decrease,` +
      `pad=${width}:${srcH}:(ow-iw)/2:(oh-ih)/2:color=black`,
    "-pix_fmt",
    "gray",
    "-f",
    "rawvideo",
    "pipe:1",
  );

  console.log(
    `[ascii-video] reading ${input} → ${width}×${srcH} grayscale @ ${fps}fps`,
  );
  const buf = await runFfmpeg(ffArgs);

  const bytesPerFrame = width * srcH;
  const numFrames = Math.floor(buf.length / bytesPerFrame);
  console.log(
    `[ascii-video] got ${numFrames} frames (${(buf.length / 1024).toFixed(1)} KB raw)`,
  );

  if (numFrames === 0) {
    console.error("No frames produced. Check input file and options.");
    process.exit(1);
  }

  const frames = [];
  for (let f = 0; f < numFrames; f++) {
    frames.push(
      frameToAscii(buf, f * bytesPerFrame, width, height, ramp, invert, tiers),
    );
  }

  emitModule({
    output,
    name,
    frames,
    meta: { input, width, height, fps, ramp },
  });

  // Final size check (gzip estimate is roughly 6-8x compression on this kind of data)
  const outBytes = frames.reduce((n, f) => n + f.length, 0);
  console.log(
    `[ascii-video] wrote ${output} (${numFrames} frames, ~${(outBytes / 1024).toFixed(1)} KB uncompressed)`,
  );
}

main().catch((e) => {
  console.error("[ascii-video] error:", e.message);
  process.exit(1);
});
