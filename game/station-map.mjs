/**
 * Mir-3 station-map blip animation primitive (m13 #161).
 *
 * Exports a canonical 76×19 ASCII schematic of the station plus a
 * frames-array generator that animates a bright "you are here" blip
 * gliding along the corridor between two rooms. The output array fits
 * the existing AsciiPlayer (game/mockups/v5-cutscene.html) — no new
 * infrastructure needed.
 *
 * Layout reference: docs/station-map.md (adjacency graph, six-port node).
 *
 * Usage:
 *   import {
 *     MIR3_MAP_BASE,
 *     ROOM_COORDS,
 *     renderMapFrame,
 *     generateTransitionFrames,
 *   } from "./station-map.mjs";
 *
 *   const frames = generateTransitionFrames("Crew Quarters", "Command Module");
 *   // frames is string[] — feed to AsciiPlayer.
 */

export const MAP_WIDTH = 76;
export const MAP_HEIGHT = 19;

/* The base map. Hand-drawn so the topology is legible. Each row is
   exactly MAP_WIDTH characters wide (verified by station-map tests). */
// biome-ignore format: hand-aligned art
const MIR3_ROWS = [
  "                            ┌──────────────┐                                ",
  "                            │ LIFE SUPPORT │                                ",
  "                            └──────┬───────┘                                ",
  " ┌─────────────┐          ┌────────┴───────┐          ┌─────────────┐       ",
  " │ HYDROPONICS ├──────────┤  CENTRAL NODE  ├──────────┤  ARMAMENT   │       ",
  " └─────────────┘          └─┬──────┬─────┬─┘          └─────────────┘       ",
  "                 ┌──────────┘      │     └────────┐                         ",
  "                 │           ┌─────┴──────┐       │                         ",
  "                 │           │ OBS CUPOLA │       │                         ",
  "                 │           └────────────┘       │                         ",
  "         ┌───────┴───────┐                ┌───────┴───────┐                 ",
  "         │ CREW QUARTERS │                │ COMMAND MODULE│                 ",
  "         └───────┬───────┘                └───────┬───────┘                 ",
  "         ┌───────┴───────┐                ┌───────┴───────┐                 ",
  "         │    REACTOR    │                │  SOYUZ FERRY  │                 ",
  "         └───────┬───────┘                └───────────────┘                 ",
  "         ┌───────┴───────┐                                                  ",
  "         │   PROGRESS    │                                                  ",
  "         └───────────────┘                                                  ",
];

export const MIR3_MAP_BASE = MIR3_ROWS.join("\n");

/* Anchor coordinates — the visible center of each room's box. The blip
   sits here when a transition starts or ends. Keys match
   game/ui.js KNOWN_ROOMS exactly. Soyuz Reentry Capsule shares the
   Soyuz Ferry coords because it's the same craft (the capsule is
   what remains after de-orbit; pre-detach it's the ferry). */
export const ROOM_COORDS = {
  "Life Support Module": { x: 35, y: 1 },
  "Hydroponics Lab": { x: 8, y: 4 },
  "Main Corridor": { x: 35, y: 4 },
  "Armament Bay": { x: 61, y: 4 },
  "Observation Cupola": { x: 35, y: 8 },
  "Crew Quarters": { x: 17, y: 11 },
  "Command Module": { x: 50, y: 11 },
  "Reactor Module": { x: 17, y: 14 },
  "Soyuz Ferry": { x: 50, y: 14 },
  "Soyuz Reentry Capsule": { x: 50, y: 14 },
  "Progress Ferry": { x: 17, y: 17 },
};

/* Adjacency graph — direct hatch connections. Listed once; the IIFE
   below mirrors each edge so BFS works regardless of which side is
   "from". Drives path-finding for non-adjacent room pairs
   (e.g. Crew → Progress routes through Reactor). Soyuz Reentry
   Capsule shares physical adjacency with Soyuz Ferry — once de-orbit
   is initiated the capsule replaces the ferry at the same hatch. */
const ADJACENCY_RAW = {
  "Main Corridor": [
    "Life Support Module",
    "Hydroponics Lab",
    "Armament Bay",
    "Observation Cupola",
    "Crew Quarters",
    "Command Module",
  ],
  "Crew Quarters": ["Reactor Module"],
  "Reactor Module": ["Progress Ferry"],
  "Command Module": ["Soyuz Ferry", "Soyuz Reentry Capsule"],
};

const ADJACENCY = (() => {
  const out = {};
  const add = (a, b) => {
    if (!out[a]) out[a] = [];
    if (!out[a].includes(b)) out[a].push(b);
  };
  for (const [a, neighbors] of Object.entries(ADJACENCY_RAW)) {
    for (const b of neighbors) {
      add(a, b);
      add(b, a);
    }
  }
  return out;
})();

/* Explicit corridor paths for each adjacent room pair. Each is a list
   of (x, y) cells from the FIRST room's anchor to the SECOND. The
   blip interpolates along these. Linear interpolation is the fallback
   when no explicit path is registered — but the L-bends here need to
   trace the visible schematic, so most edges are explicit.
   Edges are listed once and mirrored for the reverse direction. */
const EDGES_FORWARD = {
  "Main Corridor|Life Support Module": [
    { x: 35, y: 4 },
    { x: 35, y: 3 },
    { x: 35, y: 2 },
    { x: 35, y: 1 },
  ],
  "Main Corridor|Hydroponics Lab": [
    { x: 35, y: 4 },
    { x: 30, y: 4 },
    { x: 25, y: 4 },
    { x: 20, y: 4 },
    { x: 15, y: 4 },
    { x: 8, y: 4 },
  ],
  "Main Corridor|Armament Bay": [
    { x: 35, y: 4 },
    { x: 40, y: 4 },
    { x: 45, y: 4 },
    { x: 50, y: 4 },
    { x: 55, y: 4 },
    { x: 61, y: 4 },
  ],
  "Main Corridor|Observation Cupola": [
    { x: 35, y: 4 },
    { x: 35, y: 5 },
    { x: 35, y: 6 },
    { x: 35, y: 7 },
    { x: 35, y: 8 },
  ],
  "Main Corridor|Crew Quarters": [
    { x: 35, y: 4 },
    { x: 30, y: 4 },
    { x: 28, y: 5 },
    { x: 28, y: 6 },
    { x: 24, y: 6 },
    { x: 20, y: 6 },
    { x: 17, y: 6 },
    { x: 17, y: 7 },
    { x: 17, y: 8 },
    { x: 17, y: 9 },
    { x: 17, y: 10 },
    { x: 17, y: 11 },
  ],
  "Main Corridor|Command Module": [
    { x: 35, y: 4 },
    { x: 40, y: 4 },
    { x: 41, y: 5 },
    { x: 41, y: 6 },
    { x: 45, y: 6 },
    { x: 50, y: 6 },
    { x: 50, y: 7 },
    { x: 50, y: 8 },
    { x: 50, y: 9 },
    { x: 50, y: 10 },
    { x: 50, y: 11 },
  ],
  "Crew Quarters|Reactor Module": [
    { x: 17, y: 11 },
    { x: 17, y: 12 },
    { x: 17, y: 13 },
    { x: 17, y: 14 },
  ],
  "Reactor Module|Progress Ferry": [
    { x: 17, y: 14 },
    { x: 17, y: 15 },
    { x: 17, y: 16 },
    { x: 17, y: 17 },
  ],
  "Command Module|Soyuz Ferry": [
    { x: 50, y: 11 },
    { x: 50, y: 12 },
    { x: 50, y: 13 },
    { x: 50, y: 14 },
  ],
};

function edgePath(from, to) {
  const key = `${from}|${to}`;
  if (EDGES_FORWARD[key]) return EDGES_FORWARD[key];
  const reverseKey = `${to}|${from}`;
  if (EDGES_FORWARD[reverseKey])
    return EDGES_FORWARD[reverseKey].slice().reverse();
  return null;
}

/* BFS shortest path through the adjacency graph. */
function findRouteRooms(from, to) {
  if (from === to) return [from];
  const queue = [[from]];
  const seen = new Set([from]);
  while (queue.length > 0) {
    const route = queue.shift();
    const tail = route[route.length - 1];
    const neighbors = ADJACENCY[tail] || [];
    for (const next of neighbors) {
      if (seen.has(next)) continue;
      const extended = route.concat(next);
      if (next === to) return extended;
      seen.add(next);
      queue.push(extended);
    }
  }
  return null;
}

/* Concatenate per-segment edge paths into a single cell sequence.
   Drops the duplicated joining anchor between segments so the blip
   visits each cell once. Falls back to anchor-to-anchor linear
   interpolation when an edge has no explicit path (and when rooms
   are non-adjacent we route through the graph). */
function fullPath(fromRoom, toRoom) {
  const rooms = findRouteRooms(fromRoom, toRoom);
  if (!rooms) return null;
  if (rooms.length === 1) {
    const c = ROOM_COORDS[rooms[0]];
    return c ? [c] : null;
  }
  const cells = [];
  for (let i = 0; i < rooms.length - 1; i++) {
    const a = rooms[i];
    const b = rooms[i + 1];
    const seg = edgePath(a, b) || linearPath(ROOM_COORDS[a], ROOM_COORDS[b]);
    if (!seg) return null;
    if (i === 0) cells.push(...seg);
    else cells.push(...seg.slice(1));
  }
  return cells;
}

function linearPath(a, b) {
  if (!a || !b) return null;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const steps = Math.max(Math.abs(dx), Math.abs(dy));
  if (steps === 0) return [{ x: a.x, y: a.y }];
  const cells = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    cells.push({
      x: Math.round(a.x + dx * t),
      y: Math.round(a.y + dy * t),
    });
  }
  return cells;
}

/* Pick the cell on a path at fraction t ∈ [0, 1]. Clamped at both
   ends so t=0 returns the first cell and t=1 the last, even with
   floating-point drift. */
function cellAtFraction(path, t) {
  if (!path || path.length === 0) return null;
  if (path.length === 1) return path[0];
  const clamped = Math.max(0, Math.min(1, t));
  const idx = Math.min(
    path.length - 1,
    Math.floor(clamped * (path.length - 1) + 0.0001),
  );
  return path[idx];
}

/* Replace one cell in the base map with the bright blip glyph. Wraps
   the entire base map in <dim> so the schematic reads as a faded
   diagram and the blip pops against it. The blip uses U+2588 (█).
   Returns a single string (with newlines) matching MIR3_MAP_BASE
   shape, suitable for an AsciiPlayer frame. */
export function renderMapFrame(fromRoom, toRoom, t) {
  const path = fullPath(fromRoom, toRoom);
  const cell = cellAtFraction(path, typeof t === "number" ? t : 0);
  const rows = MIR3_ROWS.slice();
  if (!cell) {
    return rows.map((row) => `<dim>${row}</dim>`).join("\n");
  }
  const blipRow = rows[cell.y];
  if (blipRow === undefined) {
    return rows.map((row) => `<dim>${row}</dim>`).join("\n");
  }
  const before = blipRow.slice(0, cell.x);
  const after = blipRow.slice(cell.x + 1);
  rows[cell.y] = `<dim>${before}</dim><bri>█</bri><dim>${after}</dim>`;
  for (let i = 0; i < rows.length; i++) {
    if (i === cell.y) continue;
    rows[i] = `<dim>${rows[i]}</dim>`;
  }
  return rows.join("\n");
}

/* Generate an animated sequence of frames showing the blip moving
   from fromRoom to toRoom along the corridor path. Returns string[]
   suitable for AsciiPlayer. frameCount defaults to 14 (~1.2s at
   12fps, the v5-cutscene VIDEO_FPS default). */
export function generateTransitionFrames(fromRoom, toRoom, frameCount = 14) {
  if (frameCount < 2) frameCount = 2;
  const frames = [];
  for (let i = 0; i < frameCount; i++) {
    const t = i / (frameCount - 1);
    frames.push(renderMapFrame(fromRoom, toRoom, t));
  }
  return frames;
}

/* Helpful for tests + demo pages — exposes the resolved cell path
   for visual verification ("does the L-bend trace the schematic?"). */
export function debugPath(fromRoom, toRoom) {
  return fullPath(fromRoom, toRoom);
}

/* List of every room name with an anchor — used by the demo page to
   build the all-pairs picker. */
export const ROOM_NAMES = Object.keys(ROOM_COORDS);
