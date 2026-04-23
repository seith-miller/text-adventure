# Ship-State Simulation

`lib/ship-state.js` maintains a single JSON snapshot of every ship system, updated every turn. It is the source of truth for continuous/trending state that lives outside the Inform 7 world model.

## Public API

```js
import {
  initShipState,
  tickShipState,
  applyDelta,
  getShipState,
  renderShipStateForArgon,
} from "../lib/ship-state.js";
```

| Function | Purpose |
|----------|---------|
| `initShipState(options?)` | Reset to defaults. Optional deep-merge overrides. Call when a new game begins. |
| `tickShipState()` | Advance one turn. Orbit steps, temperature drifts, CO2 trends. Call after every MIRSEND fires. |
| `applyDelta(event, payload?)` | Apply a named state change. Covers both Inform 7 truth-state hooks and gameplay events. |
| `getShipState()` | Returns a deep-copy snapshot. Safe to read, never mutates internal state. |
| `renderShipStateForArgon()` | Translate current state into in-voice prose for the station-AI prompt. |

## Data Shape

Top-level keys: `mission`, `orbit`, `reactor`, `life_support`, `power`, `comms`, `hull`, `armament`, `propulsion`, `docked`, `crew`.

See `lib/ship-state.js` `defaultState()` for the canonical initial snapshot with all fields and their types.

### System enums

| System | Field | Valid values |
|--------|-------|-------------|
| Reactor | `state` | `idled`, `running`, `tripped`, `scrammed` |
| Reactor | `core_temp` | `nominal`, `warm`, `hot` |
| Life support | `co2_trend` | `stable`, `rising slow`, `rising fast`, `critical` |
| Life support | `temperature` | `freezing`, `cold`, `cool`, `nominal`, `warm`, `hot` |
| Power | `main_bus` | `offline`, `online` |
| Power | `isolated_bus.state` | `offline`, `online` |
| Power | `armored_bus` | `offline`, `online` |
| Propulsion | `engine` | `cold`, `firing` |
| Armament | `fire_control` | `offline`, `standby`, `online` |

No floats except `fuel_pct` (because "78% fuel" reads better than a bucket enum).

## Update Paths

### 1. Per-turn tick

`tickShipState()` advances:

- **Mission clock.** Turn counter, UTC timestamp, elapsed-since-impact.
- **Orbit.** Steps through a fixed 12-entry table cycling every 12 turns. Coarse sampling of a 92-minute orbit. Good enough for flavor.
- **Temperature.** Falls one bucket per turn while main power is offline. Stable once main power is online.
- **CO2.** Rises one step per turn with passive/offline LiOH. Falls one step with active LiOH.

### 2. Inform 7 truth-state hooks

When MIRSEND reports a truth-state flip, call `applyDelta` with the hook name. Supported hooks:

| Hook | Effect |
|------|--------|
| `power-is-restored` | Main bus, armored bus, reactor, O2 gen, LiOH all come online |
| `armament-bay-unlocked` | Bay hatch unlocked, fire control to standby |
| `corridor-pressurized` | Central node sealed |
| `reactor-scrammed` | Reactor scrammed, pumps stopped, core hot |
| `reactor-tripped` | Reactor tripped, core warm |
| `comms-restored` | Signal floor weak, Freedom Station live channel open |
| `hull-breach-sealed` | Central node sealed |
| `engine-fired` | Engine to firing |
| `engine-shutdown` | Engine to cold |
| `soyuz-detached` | Soyuz detached |
| `progress-detached` | Progress detached |

### 3. Gameplay event deltas

| Event | Payload | Effect |
|-------|---------|--------|
| `cannon_fired` | none | Decrement shells (min 0) |
| `dosimeter_taken` | none | Add dosimeter to crew.equipped |
| `fire_control_activated` | none | Fire control online |
| `fire_control_deactivated` | none | Fire control offline |
| `isolated_bus_feeds_changed` | `{ feeds: string[] }` | Update isolated bus feeds |
| `coolant_pump_failed` | none | Decrement running pumps |
| `coolant_pump_restarted` | none | Increment running pumps |
| `crew_found_alive` | `{ name: string }` | Move from unknown to known_alive |
| `crew_found_dead` | `{ name: string }` | Move from unknown to known_dead |
| `fuel_consumed` | `{ amount: number }` | Reduce fuel_pct and delta_v |

Unknown events throw. No arbitrary writes.

## Orbit Table

12 entries cycling every 12 turns. Each entry: `{ lat, lon, region, lit }`.

The table represents a coarse sampling of a ~92-minute LEO orbit at 51.6 deg inclination. Regions are flavor text. Day/night side is approximate.

## Voice Translation

`renderShipStateForArgon()` converts the snapshot into prose blocks:

```
[Time onboard] Mission clock HH:MM Moscow, N minutes since the impact.
[Where we are] Altitude in words. Region. Lighting.
[My systems]
  Reactor: ...
  Life support: ...
  Main power: ...
  ...
```

The translator follows `docs/writing-style.md`:
- No em-dashes. Ever.
- Fragmented rhythm.
- Ritual exactness (spelled-out numbers for altitude).
- No assistant tone.

The golden-file test at `tests/golden/ship-state-voice-default.txt` catches regressions.

## How to Extend

### Adding a new system

1. Add the default fields to `defaultState()` in `lib/ship-state.js`.
2. If the system ticks per-turn, add logic to `tickShipState()`.
3. Add a section to `renderShipStateForArgon()`.
4. Update tests and the golden file.

### Adding a new event

1. Add a handler to `EVENT_HANDLERS` (gameplay) or `TRUTH_STATE_MAP` (Inform 7 hook).
2. Add a test in `tests/test_ship_state.py`.
3. Update this document.

### Adding an orbit step

Append to `ORBIT_TABLE`. The cycle length is `ORBIT_TABLE.length`, so adding a 13th entry makes the cycle 13 turns automatically.

## Testing

- **Unit tests:** `python3 -m pytest tests/test_ship_state.py -v`
- **Voice golden-file:** `python3 -m pytest tests/test_ship_state_voice.py -v`
- **Playwright integration:** `npx playwright test tests/e2e/ship-state-integration.spec.ts`

## Dependencies

- Consumed by: shared LLM bridge (#61), Argon-87 station AI (#62)
- No runtime dependencies. Pure ES module.
