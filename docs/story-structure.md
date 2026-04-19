# MIR'S END — Story Structure

Single source of truth for the shape of the story. Regenerate this
document when the branching changes. Keep it diagrammatic — no prose
that isn't in the game source.

## Map

```
                             ┌─────────────────────┐
                             │  Observation Cupola │
                             │  — viewport (war)   │
                             └──────────┬──────────┘
                                        │ E / W
                                        │
  ┌───────────────┐   N / S   ┌─────────┴─────────┐   N / S   ┌──────────────────┐
  │ Crew Quarters │───────────│    Main Corridor   │───────────│  Command Module  │
  │ (start here)  │           │  (Yevgenia, Petrov)│           │  (console, comms)│
  └───────────────┘           └────────────────────┘           └──────────────────┘
```

Four rooms. Darkness gates the first north move until the flashlight is lit.

## Act structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ACT 1  —  Wake in darkness                                            │
│     opening narrative → Crew Quarters                                   │
│     locker + flashlight + listen-for-tapping                            │
│                                                                         │
│  ACT 2  —  Meet the crew                                               │
│     Main Corridor: Yevgenia Kozlova (engineer), Commander Petrov       │
│     ASK ABOUT topics: emp, war, power, selengrad, americans, etc.      │
│                                                                         │
│  ACT 3  —  The viewport                                                │
│     Observation Cupola: EXAMINE VIEWPORT → nuclear exchange revealed   │
│     Morale −15 (war-is-discovered = true from here on)                 │
│                                                                         │
│  ACT 4  —  Restoring power                                             │
│     Command Module: open toolkit → take multimeter → restore power     │
│     power-is-restored = true, console flickers on, Yevgenia arrives    │
│                                                                         │
│  ACT 5  —  The distress call                                           │
│     LISTEN at powered comms → Freedom Station (Chen), distress-call-   │
│     heard = true                                                        │
│                                                                         │
│  ACT 6  —  The only fork in the prototype                              │
│                                                                         │
│         ┌── TRANSMIT ──→ Commander Chen answers live.                  │
│         │                Selengrad plan agreed. "Begin preparations."  │
│         │                Morale +8. responded-to-americans = true.     │
│         │                                                               │
│     ────┤                                                               │
│         │                                                               │
│         └── STAY SILENT → Petrov responds anyway. Dark descent.        │
│                            Morale −8.                                   │
│                                                                         │
│     [PROTOTYPE BOUNDARY]                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

## State variables (Inform 7 truth states)

| Variable                 | Set by                                       | Gates                                    |
|--------------------------|----------------------------------------------|------------------------------------------|
| `chemical flashlight is lit` | Switch on flashlight                         | Movement north from Crew Quarters        |
| `listening-to-tapping`   | First LISTEN in Crew Quarters                | Morale bump, one-shot                    |
| `war-is-discovered`      | First EXAMINE VIEWPORT in Cupola             | Cupola room description, Petrov NPC move |
| `power-is-restored`      | RESTORE POWER in Command Module w/ multimeter| Command Module description, LISTEN call  |
| `distress-call-heard`    | LISTEN in Command Module w/ power restored   | TRANSMIT gate                            |
| `responded-to-americans` | TRANSMIT                                     | Story climax text                        |

## Resources

| Resource | Start | Change per turn | Kill at                |
|----------|-------|-----------------|------------------------|
| Oxygen   | 100   | −1              | 0 → end: "You have suffocated" |
| Morale   | 50    | event-driven    | no hard floor (display-only)   |
| Score    | 0     | event-driven    | max 10                 |

## Morale events

| Event                         | Δ    |
|-------------------------------|------|
| Switch on flashlight (first)  | +5   |
| Listen in Crew Quarters (first)| +3  |
| Examine viewport (first)      | −15  |
| Restore power (first)         | +10  |
| Transmit (answer Chen)        | +8   |
| Stay silent                   | −8   |

## NPC movement

- **Yevgenia** arrives in the Command Module once power is restored
  (every-turn rule while `power-is-restored is true and Yevgenia is
  not in Command Module`).
- **Petrov** drifts into the Cupola when the player is there and the
  war has been discovered (every-turn rule).
- Both can be asked about overlapping topics with different voices
  (Yevgenia: pragmatic; Petrov: military).

## What's NOT in the prototype

- The Moon flight itself. The game ends at "Begin preparations."
- Any branching beyond TRANSMIT / STAY SILENT.
- Random or probabilistic outcomes. Every state is deterministic.
- Inventory puzzles more complex than flashlight + multimeter.
- Radiation (planned).
- The station's hidden cannon (planned — historical: real armed
  Almaz stations carried a Rikhter R-23).

## Updating this doc

The acts and state variables are grep-able. If you add a new truth
state to `story.ni`, add a row to the State Variables table. If you
add a new event with a morale delta, add a row. If the map changes,
redraw the ASCII. CI doesn't enforce this — it's on us to keep it
honest.
