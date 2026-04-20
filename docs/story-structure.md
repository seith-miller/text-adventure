# MIR'S END — Story Structure

Single source of truth for the shape of the story. Regenerate this
document when the branching changes. Keep it diagrammatic — no prose
that isn't in the game source.

## Map

```
                             ┌─────────────────────┐
                             │  Observation Cupola │
                             │  Petrov's body      │
                             │  viewport (WWIII)   │
                             └──────────┬──────────┘
                                        │ E / W
                                        │
  ┌───────────────┐   N / S   ┌─────────┴─────────┐   N / S   ┌──────────────────┐
  │ Crew Quarters │───────────│    Main Corridor   │───────────│  Command Module  │
  │ (start here)  │           │  Yevgenia's body   │           │  console, comms, │
  │ sealed hatch  │           │  (notebook on her) │           │  classified safe │
  └───────────────┘           └────────────────────┘           └──────────────────┘
```

Four rooms. Two gates leaving Crew Quarters: flashlight unlit (darkness)
AND corridor in vacuum (pressure equalization valve must be opened).

## Act structure (solo player; crew dead in the prologue impact)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PROLOGUE  —  The shock                                                │
│     ASAT-grade kinetic strike on Mir-3's central service node.         │
│     Hub depressurizes. Crew (Yevgenia + Petrov) die in vacuum within   │
│     seconds. Player survives because their bunk module sealed via a    │
│     passive mechanical pressure-differential valve. EMP also hit       │
│     simultaneously (or just before): all electronics dead.             │
│                                                                         │
│  ACT 1  —  Wake alone                                                  │
│     Crew Quarters in darkness. Find flashlight in locker, switch on.   │
│     LISTEN: silence. No human sound. Morale −3 (you understand).       │
│     EXAMINE HATCH: sealed by pressure differential. Use the manual     │
│     equalization valve to vent your air into the corridor. Hatch       │
│     opens. You have just shared half your air with vacuum.             │
│                                                                         │
│  ACT 2  —  The dead                                                    │
│     Main Corridor: frost, drifting debris, Yevgenia's body floating    │
│     by the maintenance panel. EXAMINE her, take her flight notebook.   │
│     READ NOTEBOOK: EMP confirmed (military grade), power-restore       │
│     sequence, Selengrad math, Petrov-must-authorize note.              │
│                                                                         │
│  ACT 3  —  The viewport                                                │
│     Observation Cupola: Petrov's body at the hatch wheel — he was      │
│     trying to confirm the strike with his eyes. EXAMINE VIEWPORT →     │
│     hundreds of thermonuclear flashes still blooming below. WW3, live, │
│     in real time. Morale −15. war-is-discovered = true.                │
│                                                                         │
│  ACT 4  —  Restore power, alone                                        │
│     Command Module: open toolkit → take multimeter → restore power.    │
│     Solo: the action requires both the multimeter AND Yevgenia's       │
│     notebook (you follow her handwritten reset sequence).              │
│     Console flickers on. power-is-restored = true.                     │
│                                                                         │
│  ACT 5  —  The log and the secret                                      │
│     READ LOG: Petrov's last entry, dictated 03:52, minutes before      │
│     the impact at 03:54. Reveals a "second object inbound" he did not  │
│     recognize. Reveals the existence of a classified armament bay on   │
│     this module. Gives the arming sequence: 3-7-1-1.                   │
│     EXAMINE SAFE: keypad-locked. After log read, OPEN SAFE accepts     │
│     the code — green light, magnetic click, no power yet to operate    │
│     the weapon (deferred to later PR).                                 │
│                                                                         │
│  ACT 6  —  The distress call                                           │
│     LISTEN at powered comms → Freedom Station (Chen) on emergency      │
│     loop. Five American survivors, two injured.                        │
│     distress-call-heard = true.                                         │
│                                                                         │
│  ACT 7  —  The choice (prototype climax)                               │
│                                                                         │
│         ┌── TRANSMIT ──→ You key the mic alone. Chen answers live.     │
│         │                You propose Selengrad from Yevgenia's notes.  │
│         │                Five Americans + you. "Begin preparations."   │
│         │                Morale +8.                                    │
│         │                                                               │
│     ────┤                                                               │
│         │                                                               │
│         └── STAY SILENT → You let the loop fade. Morale −8.            │
│                            Notebook math: alone you cannot make        │
│                            Selengrad. The fuel arithmetic is fixed.    │
│                            chose-silence = true. Can still change      │
│                            mind until the loop is gone.                │
│                                                                         │
│     [PROTOTYPE BOUNDARY]                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

## State variables (Inform 7 truth states)

| Variable                 | Set by                                       | Gates                                    |
|--------------------------|----------------------------------------------|------------------------------------------|
| `chemical flashlight is lit` | Switch on flashlight                         | Movement north (gate 1: darkness)        |
| `corridor-pressurized`   | OPEN/PULL pressure valve                     | Movement north (gate 2: vacuum)          |
| `listening-to-station`   | First LISTEN in Crew Quarters                | Solo realization beat, morale −3         |
| `war-is-discovered`      | First EXAMINE VIEWPORT in Cupola             | Cupola room description                  |
| `power-is-restored`      | RESTORE POWER (needs multimeter + notebook)  | Console, comms, log readability          |
| `distress-call-heard`    | LISTEN in Command Module w/ power restored   | TRANSMIT gate                            |
| `responded-to-americans` | TRANSMIT                                     | Selengrad story branch                   |
| `chose-silence`          | STAY SILENT                                  | Alternative branch                       |
| `petrov-log-read`        | READ LOG (needs power)                       | Cannon arming code visible to safe       |

## Resources

| Resource | Start | Change per turn | Kill at                |
|----------|-------|-----------------|------------------------|
| Oxygen   | 100   | −1              | 0 → end: "You have suffocated" |
| Morale   | 50    | event-driven    | no hard floor (display-only)   |
| Score    | 0     | event-driven    | max 12                 |

## Morale events

| Event                          | Δ    |
|--------------------------------|------|
| Switch on flashlight (first)   | +5   |
| Listen in Crew Quarters (first)| **−3** (you confirm you are alone) |
| Examine viewport (first)       | −15  |
| Restore power (first)          | +10  |
| Listen → distress call         | +3   |
| Transmit (answer Chen)         | +8   |
| Stay silent                    | −8   |

## Artifacts replacing dialogue

The crew is dead in the prologue, so the information they used to give
through ASK ABOUT now lives in two artifacts:

- **Yevgenia's notebook** (clipped to her body, takeable, readable):
  EMP confirmation, power-restore sequence, life support timeline,
  Selengrad math + caretaker status.
- **Petrov's last log** (on the command console, requires power):
  EMP timestamp, "second object inbound" note, classified armament
  bay disclosure, arming code 3-7-1-1, final orders to whoever reads
  it: "do what you can. Make it worth something."

## What's NOT in the prototype

- The Moon flight itself. The game ends at "Begin preparations."
- The cannon firing mechanic. The safe opens (magnetic click) but the
  weapon is not yet wired to a fire-control console. See
  [world/systems/cannon.md](../world/systems/cannon.md).
- Random or probabilistic outcomes. Every state is deterministic.
- Inventory puzzles more complex than flashlight + multimeter +
  notebook.
- Radiation (planned).

## Updating this doc

The acts and state variables are grep-able. If you add a new truth
state to `story.ni`, add a row to the State Variables table. If you
add a new event with a morale delta, add a row. If the map changes,
redraw the ASCII. CI doesn't enforce this — it's on us to keep it
honest.
