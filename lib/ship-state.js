/**
 * Ship-state simulation module for Mir's End.
 *
 * Maintains a single JSON snapshot of every ship system, updated each turn.
 * Consumers read via getShipState(); the shared LLM bridge reads via
 * renderShipStateForArgon() to feed prose context to the station-AI role.
 *
 * Three update paths:
 *   1. Inform 7 truth-state hooks  (applyDelta with mapped event names)
 *   2. Per-turn tick                (tickShipState)
 *   3. Explicit gameplay deltas     (applyDelta with whitelisted events)
 */

// ── Orbit lookup table (12 steps, ~92-minute period) ────────────────────────

const ORBIT_TABLE = [
  { lat: 51, lon: 37, region: "over Russia (Moscow corridor)", lit: true },
  { lat: 47, lon: 17, region: "over Russia (Volga)", lit: true },
  { lat: 30, lon: 5, region: "over the Mediterranean", lit: true },
  { lat: 10, lon: -20, region: "over the Atlantic", lit: true },
  { lat: -10, lon: -45, region: "over Brazil", lit: false },
  { lat: -30, lon: -65, region: "over Argentina", lit: false },
  { lat: -45, lon: -100, region: "over the South Pacific", lit: false },
  { lat: -30, lon: -130, region: "over the Pacific", lit: false },
  { lat: -10, lon: -155, region: "over the central Pacific", lit: false },
  { lat: 10, lon: -170, region: "over the North Pacific", lit: true },
  { lat: 30, lon: 160, region: "over Japan", lit: true },
  { lat: 45, lon: 100, region: "over central Asia", lit: true },
];

// ── Temperature drift rules ─────────────────────────────────────────────────

const TEMP_BUCKETS = ["freezing", "cold", "cool", "nominal", "warm", "hot"];

function driftTemp(current, direction) {
  const idx = TEMP_BUCKETS.indexOf(current);
  if (idx === -1) return current;
  if (direction === "falling") return TEMP_BUCKETS[Math.max(0, idx - 1)];
  if (direction === "rising") return TEMP_BUCKETS[Math.min(TEMP_BUCKETS.length - 1, idx + 1)];
  return current;
}

// ── CO2 drift rules ─────────────────────────────────────────────────────────

const CO2_LEVELS = ["stable", "rising slow", "rising fast", "critical"];

function driftCO2(current, liohMode) {
  const idx = CO2_LEVELS.indexOf(current);
  if (idx === -1) return current;
  if (liohMode === "active") {
    // Active scrubbing pushes CO2 down
    return CO2_LEVELS[Math.max(0, idx - 1)];
  }
  // Passive or offline: CO2 rises one step
  return CO2_LEVELS[Math.min(CO2_LEVELS.length - 1, idx + 1)];
}

// ── Mission clock helpers ───────────────────────────────────────────────────

const IMPACT_TIME = new Date("1987-10-24T03:01:27Z");
const SECONDS_PER_TURN = 67; // ~92 min orbit / 12 steps ≈ 460s, but gameplay turns are shorter

function formatElapsed(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const h = String(Math.floor(totalSeconds / 3600)).padStart(2, "0");
  const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const s = String(totalSeconds % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

// ── Internal state ──────────────────────────────────────────────────────────

let shipState = null;

function defaultState() {
  return {
    mission: {
      turn: 0,
      clock_utc: "1987-10-24T03:01:27Z",
      elapsed_since_impact: "00:00:00",
    },
    orbit: {
      altitude_km: 352,
      inclination_deg: 51.6,
      ground_track_lat: 51,
      ground_track_lon: 37,
      region: "over Russia (Moscow corridor)",
      lit_side: true,
      time_to_terminator_s: 1240,
    },
    reactor: {
      state: "idled",
      coolant_pumps: { running: 2, total: 3 },
      core_temp: "nominal",
      rad_output_mSvh: 0.003,
    },
    life_support: {
      o2_generator: "offline",
      lioh_mode: "passive",
      co2_trend: "rising slow",
      temperature: "nominal",
      temp_direction: "falling",
      water_recycler: "online",
    },
    power: {
      main_bus: "offline",
      isolated_bus: { state: "online", feeds: ["status_console", "comms_array"] },
      armored_bus: "offline",
    },
    comms: {
      array: "patched to isolated bus",
      signal_floor: "static",
      contacts: {
        freedom_station: { last_heard: "distress loop", live_channel: false },
        selengrad: { last_heard: "silent", caretaker_mode: true },
        baikonur: { carrier: false, assumed_lost: true },
      },
    },
    hull: {
      central_node: "breached, sealed",
      other_modules: "nominal",
    },
    armament: {
      bay_hatch: "unlocked",
      fire_control: "offline",
      shells_remaining: 3,
    },
    propulsion: {
      fuel_pct: 78,
      engine: "cold",
      delta_v_available_mps: 340,
    },
    docked: {
      soyuz: "nominal",
      progress: "battery intact",
    },
    crew: {
      known_alive: ["self"],
      known_dead: ["Kozlova", "Petrov"],
      unknown: [],
    },
  };
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Initialize ship state for a new game.
 * @param {object} [options] - Optional overrides merged onto default state.
 */
export function initShipState(options = {}) {
  shipState = defaultState();
  if (options && typeof options === "object") {
    deepMerge(shipState, options);
  }
  return getShipState();
}

/**
 * Advance ship state by one turn. Called after every MIRSEND fires.
 */
export function tickShipState() {
  if (!shipState) throw new Error("Ship state not initialized. Call initShipState() first.");

  // Advance turn counter
  shipState.mission.turn += 1;

  // Advance mission clock
  const elapsedMs = shipState.mission.turn * SECONDS_PER_TURN * 1000;
  const currentTime = new Date(IMPACT_TIME.getTime() + elapsedMs);
  shipState.mission.clock_utc = currentTime.toISOString().replace(".000Z", "Z");
  shipState.mission.elapsed_since_impact = formatElapsed(elapsedMs);

  // Advance orbit (12-step cycle)
  const orbitIdx = shipState.mission.turn % 12;
  const orbitEntry = ORBIT_TABLE[orbitIdx];
  shipState.orbit.ground_track_lat = orbitEntry.lat;
  shipState.orbit.ground_track_lon = orbitEntry.lon;
  shipState.orbit.region = orbitEntry.region;
  shipState.orbit.lit_side = orbitEntry.lit;

  // Estimate time to terminator (rough: steps until lit flips)
  let stepsToFlip = 0;
  for (let i = 1; i <= 12; i++) {
    const nextIdx = (orbitIdx + i) % 12;
    if (ORBIT_TABLE[nextIdx].lit !== orbitEntry.lit) {
      stepsToFlip = i;
      break;
    }
  }
  shipState.orbit.time_to_terminator_s = stepsToFlip * SECONDS_PER_TURN;

  // Temperature drift: falling while main power is out, stable once restored
  const tempDirection = shipState.power.main_bus === "online" ? "stable" : "falling";
  shipState.life_support.temp_direction = tempDirection;
  shipState.life_support.temperature = driftTemp(
    shipState.life_support.temperature,
    tempDirection,
  );

  // CO2 drift based on LiOH mode
  shipState.life_support.co2_trend = driftCO2(
    shipState.life_support.co2_trend,
    shipState.life_support.lioh_mode,
  );

  return getShipState();
}

// ── Truth-state mapping (Inform 7 flags → structured deltas) ────────────────

const TRUTH_STATE_MAP = {
  "power-is-restored": (state) => {
    state.power.main_bus = "online";
    state.power.armored_bus = "online";
    state.reactor.state = "running";
    state.life_support.o2_generator = "online";
    state.life_support.lioh_mode = "active";
  },
  "armament-bay-unlocked": (state) => {
    state.armament.bay_hatch = "unlocked";
    state.armament.fire_control = "standby";
  },
  "corridor-pressurized": (state) => {
    state.hull.central_node = "breached, sealed";
  },
  "reactor-scrammed": (state) => {
    state.reactor.state = "scrammed";
    state.reactor.coolant_pumps.running = 0;
    state.reactor.core_temp = "hot";
  },
  "reactor-tripped": (state) => {
    state.reactor.state = "tripped";
    state.reactor.core_temp = "warm";
  },
  "comms-restored": (state) => {
    state.comms.signal_floor = "weak";
    state.comms.contacts.freedom_station.live_channel = true;
  },
  "hull-breach-sealed": (state) => {
    state.hull.central_node = "breached, sealed";
  },
  "engine-fired": (state) => {
    state.propulsion.engine = "firing";
  },
  "engine-shutdown": (state) => {
    state.propulsion.engine = "cold";
  },
  "soyuz-detached": (state) => {
    state.docked.soyuz = "detached";
  },
  "progress-detached": (state) => {
    state.docked.progress = "detached";
  },
};

// ── Gameplay event deltas (whitelisted) ─────────────────────────────────────

const EVENT_HANDLERS = {
  cannon_fired: (state) => {
    if (state.armament.shells_remaining > 0) {
      state.armament.shells_remaining -= 1;
    }
  },
  dosimeter_taken: (state) => {
    if (!state.crew.equipped) state.crew.equipped = [];
    if (!state.crew.equipped.includes("dosimeter")) {
      state.crew.equipped.push("dosimeter");
    }
  },
  fire_control_activated: (state) => {
    state.armament.fire_control = "online";
  },
  fire_control_deactivated: (state) => {
    state.armament.fire_control = "offline";
  },
  isolated_bus_feeds_changed: (state, payload) => {
    if (payload && Array.isArray(payload.feeds)) {
      state.power.isolated_bus.feeds = payload.feeds;
    }
  },
  coolant_pump_failed: (state) => {
    state.reactor.coolant_pumps.running = Math.max(0, state.reactor.coolant_pumps.running - 1);
  },
  coolant_pump_restarted: (state) => {
    state.reactor.coolant_pumps.running = Math.min(
      state.reactor.coolant_pumps.total,
      state.reactor.coolant_pumps.running + 1,
    );
  },
  crew_found_alive: (state, payload) => {
    if (payload && payload.name) {
      state.crew.unknown = state.crew.unknown.filter((n) => n !== payload.name);
      if (!state.crew.known_alive.includes(payload.name)) {
        state.crew.known_alive.push(payload.name);
      }
    }
  },
  crew_found_dead: (state, payload) => {
    if (payload && payload.name) {
      state.crew.unknown = state.crew.unknown.filter((n) => n !== payload.name);
      if (!state.crew.known_dead.includes(payload.name)) {
        state.crew.known_dead.push(payload.name);
      }
    }
  },
  fuel_consumed: (state, payload) => {
    if (payload && typeof payload.amount === "number") {
      state.propulsion.fuel_pct = Math.max(0, state.propulsion.fuel_pct - payload.amount);
      // Rough delta-v proportional to fuel
      state.propulsion.delta_v_available_mps = Math.round(
        (state.propulsion.fuel_pct / 100) * 436,
      );
    }
  },
};

/**
 * Apply a named delta to ship state.
 * @param {string} event - Whitelisted event name or truth-state hook.
 * @param {object} [payload] - Optional payload for events that need parameters.
 */
export function applyDelta(event, payload = {}) {
  if (!shipState) throw new Error("Ship state not initialized. Call initShipState() first.");

  // Check truth-state hooks first
  if (TRUTH_STATE_MAP[event]) {
    TRUTH_STATE_MAP[event](shipState);
    return getShipState();
  }

  // Check gameplay event handlers
  if (EVENT_HANDLERS[event]) {
    EVENT_HANDLERS[event](shipState, payload);
    return getShipState();
  }

  throw new Error(`Unknown event: "${event}". Not in truth-state map or event whitelist.`);
}

/**
 * Return a deep-frozen read-only snapshot of current ship state.
 */
export function getShipState() {
  if (!shipState) throw new Error("Ship state not initialized. Call initShipState() first.");
  return JSON.parse(JSON.stringify(shipState));
}

// ── Voice translation for Argon-87 ─────────────────────────────────────────

/**
 * Render the current ship state as in-voice prose for the station-AI prompt.
 * No em-dashes. Fragmented rhythm. Ritual exactness.
 */
export function renderShipStateForArgon() {
  if (!shipState) throw new Error("Ship state not initialized. Call initShipState() first.");
  const s = shipState;
  const lines = [];

  // Time block
  const clockDate = new Date(s.mission.clock_utc);
  const hours = String(clockDate.getUTCHours()).padStart(2, "0");
  const minutes = String(clockDate.getUTCMinutes()).padStart(2, "0");
  lines.push(
    `[Time onboard] Mission clock ${hours}:${minutes} Moscow, ${formatElapsedProse(s.mission.elapsed_since_impact)} since the impact.`,
  );

  // Orbit block
  const altText = numberToWords(s.orbit.altitude_km);
  const litText = s.orbit.lit_side ? "Sunlit side" : "Shadow side";
  const terminatorText =
    s.orbit.time_to_terminator_s > 0
      ? `${litText} for another ${Math.round(s.orbit.time_to_terminator_s / 60)} minutes.`
      : `${litText}. Terminator crossing imminent.`;
  lines.push(
    `[Where we are] ${altText} kilometres up. Crossing ${s.orbit.region.replace("over ", "")} eastbound. ${terminatorText}`,
  );

  // Systems block
  lines.push("[My systems]");

  // Reactor
  const pumpText = buildPumpText(s.reactor.coolant_pumps);
  lines.push(
    `  Reactor: ${s.reactor.state}. ${pumpText} Core temperature ${s.reactor.core_temp}. Radiation output ${s.reactor.rad_output_mSvh} mSv/h.`,
  );

  // Life support
  const tempText = formatTemperature(s.life_support.temperature, s.life_support.temp_direction);
  const o2Text = s.life_support.o2_generator;
  const liohText =
    s.life_support.lioh_mode === "active" ? "LiOH active scrubbing" : "LiOH passive is holding";
  const co2Text = `CO2 is ${s.life_support.co2_trend}`;
  lines.push(
    `  Life support: O2 generator ${o2Text}. ${liohText}. ${co2Text}. The temperature is ${tempText}. Water recycler ${s.life_support.water_recycler}.`,
  );

  // Power
  const mainText = `Main power: ${s.power.main_bus}`;
  let busText = "";
  if (s.power.isolated_bus.state === "online") {
    busText = `. One isolated bus is live, feeding ${s.power.isolated_bus.feeds.join(" and ")}`;
  }
  const armoredText =
    s.power.armored_bus !== "offline" ? `. Armored bus ${s.power.armored_bus}` : "";
  lines.push(`  ${mainText}${busText}${armoredText}.`);

  // Comms
  lines.push(`  Comms array: ${s.comms.array}. Signal floor: ${s.comms.signal_floor}.`);
  for (const [name, info] of Object.entries(s.comms.contacts)) {
    const displayName = name.replace(/_/g, " ");
    const contactParts = [];
    if (info.last_heard) contactParts.push(info.last_heard);
    if (info.live_channel) contactParts.push("live channel open");
    if (info.caretaker_mode) contactParts.push("caretaker mode");
    if (info.assumed_lost) contactParts.push("assumed lost");
    if (info.carrier === false && !info.assumed_lost) contactParts.push("no carrier");
    lines.push(`    ${capitalize(displayName)}: ${contactParts.join(". ")}.`);
  }

  // Hull
  lines.push(
    `  Hull: central node ${s.hull.central_node}. Other modules ${s.hull.other_modules}.`,
  );

  // Armament
  lines.push(
    `  Armament: bay hatch ${s.armament.bay_hatch}. Fire control ${s.armament.fire_control}. ${s.armament.shells_remaining} shells remaining.`,
  );

  // Propulsion
  lines.push(
    `  Propulsion: ${s.propulsion.fuel_pct} percent fuel. Engine ${s.propulsion.engine}. ${s.propulsion.delta_v_available_mps} m/s delta-v available.`,
  );

  // Docked
  lines.push(`  Docked: Soyuz ${s.docked.soyuz}. Progress ${s.docked.progress}.`);

  // Crew
  const aliveText = s.crew.known_alive.join(", ");
  const deadText = s.crew.known_dead.length > 0 ? s.crew.known_dead.join(", ") : "none confirmed";
  lines.push(`  Crew: alive ${aliveText}. Dead: ${deadText}.`);
  if (s.crew.unknown && s.crew.unknown.length > 0) {
    lines.push(`    Unaccounted: ${s.crew.unknown.join(", ")}.`);
  }

  return lines.join("\n");
}

// ── Prose helpers ───────────────────────────────────────────────────────────

function formatElapsedProse(elapsed) {
  const parts = elapsed.split(":");
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  const pieces = [];
  if (h > 0) pieces.push(`${h} hour${h !== 1 ? "s" : ""}`);
  if (m > 0) pieces.push(`${m} minute${m !== 1 ? "s" : ""}`);
  if (pieces.length === 0) return "moments";
  return pieces.join(" and ");
}

function numberToWords(n) {
  // Simple conversion for altitude range (300-400)
  const hundreds = Math.floor(n / 100);
  const remainder = n % 100;
  const hundredWords = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
  const tensWords = [
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
  ];
  const onesWords = [
    "",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
  ];

  let result = "";
  if (hundreds > 0) {
    result += `${hundredWords[hundreds]} hundred`;
  }
  if (remainder > 0) {
    if (result) result += " ";
    if (remainder < 20) {
      result += onesWords[remainder];
    } else {
      const tens = Math.floor(remainder / 10);
      const ones = remainder % 10;
      result += tensWords[tens];
      if (ones > 0) result += `-${onesWords[ones]}`;
    }
  }
  return result.charAt(0).toUpperCase() + result.slice(1);
}

function buildPumpText(pumps) {
  if (pumps.running === 0) return "All coolant pumps stopped.";
  if (pumps.running === pumps.total) return `All ${pumps.total} coolant pumps running.`;
  const stopped = pumps.total - pumps.running;
  return `${capitalize(numberWordSmall(pumps.running))} coolant pump${pumps.running !== 1 ? "s" : ""} still running. ${capitalize(numberWordSmall(stopped))} ha${stopped !== 1 ? "ve" : "s"} stopped.`;
}

function numberWordSmall(n) {
  const words = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
  ];
  return n < words.length ? words[n] : String(n);
}

function formatTemperature(bucket, direction) {
  if (direction === "stable" || direction === undefined) return bucket;
  return `${bucket} and ${direction}`;
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Deep merge utility ──────────────────────────────────────────────────────

function deepMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (
      source[key] &&
      typeof source[key] === "object" &&
      !Array.isArray(source[key]) &&
      target[key] &&
      typeof target[key] === "object" &&
      !Array.isArray(target[key])
    ) {
      deepMerge(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
}

// ── Exports for testing internals ───────────────────────────────────────────

export const _internals = {
  ORBIT_TABLE,
  TEMP_BUCKETS,
  CO2_LEVELS,
  TRUTH_STATE_MAP,
  EVENT_HANDLERS,
  SECONDS_PER_TURN,
};
