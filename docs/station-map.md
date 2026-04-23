# Mir-3 — Station Map (design doc, pre-implementation)

Alt-history 1988. A larger, militarized, nuclear-powered successor to Mir.
Modular architecture inherited from the DOS-7 / DOS-8 lineage; expanded
beyond the real Mir's four-radial-port layout into a full six-port central
node plus chained modules.

## Layout (ASCII schematic)

```
                          ┌──────────────────┐
                          │   LIFE SUPPORT    │
                          │   (zenith)        │
                          └────────┬─────────┘
                                   │ UP
                                   │
  ┌─────────────┐  PORT   ┌────────┴─────────┐  STARBOARD  ┌─────────────┐
  │ HYDROPONICS │ ←─────  │   CENTRAL NODE    │  ───────→   │ ARMAMENT BAY │
  │   LAB       │         │  (Main Corridor)  │             │ [CLASSIFIED] │
  └─────────────┘         └────────┬─────────┘             └─────────────┘
                                   │ DOWN
                                   │
                          ┌────────┴─────────┐
                          │ OBSERVATION       │
                          │   CUPOLA          │
                          │   (nadir)         │
                          └──────────────────┘

  Fore-aft axis:
  ┌──────────┐   AFT   ┌──────────────┐  FORE   ┌─────────────┐
  │  CREW    │ ←──────  │ CENTRAL NODE  │  ─────→ │  COMMAND    │
  │ QUARTERS │         └──────────────┘         │  MODULE      │
  └────┬─────┘                                  └──────┬──────┘
       │ AFT                                          │ STARBOARD
       │                                              │
  ┌────┴─────┐   STARBOARD   ┌─────────────┐    ┌────┴─────┐
  │  REACTOR │ ────────────→ │  PROGRESS    │    │  SOYUZ   │
  │  MODULE  │              │  (docked)    │    │ (docked) │
  └──────────┘              └─────────────┘    └──────────┘
```

## Ten modules, each with 6 faces

Every module is mechanically **rectangular** (N/S/E/W/UP/DOWN) even though
described as a cylinder or sphere. Each of the six faces has one feature
— a hatch, a console, a locker, a bunk, a panel. `EXAMINE <noun>` on any
of those features reaches into that face.

The map uses these direction conventions:

| Game direction | Station axis       |
|----------------|--------------------|
| NORTH          | fore (forward)     |
| SOUTH          | aft (stern)        |
| EAST           | starboard          |
| WEST           | port               |
| UP             | zenith             |
| DOWN           | nadir              |

## Module-by-module

### 1. Central Node (current "Main Corridor")

The six-port junction. Yevgenia's body drifts here.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| FORE       | **Hatch → Command Module**                                        |
| AFT        | **Hatch → Crew Quarters**                                         |
| PORT       | **Hatch → Hydroponics Lab**                                       |
| STARBOARD  | **Hatch → Armament Bay** (classified marking, initially unreadable) |
| ZENITH     | **Hatch → Life Support**                                          |
| NADIR      | **Hatch → Observation Cupola**                                    |

Floating in the node volume: Yevgenia, the clipboard, the flight manual, the mug.

### 2. Crew Quarters

Your bunk module. Current starting position.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| FORE       | **Hatch → Central Node** (sealed by pressure differential at start) |
| AFT        | **Hatch → Reactor Module** (sealed — requires dosimeter to enter safely) |
| PORT       | Four sleeping bunks (strapped). The sleeping harness you woke in. |
| STARBOARD  | **Emergency locker** (has the flashlight). Personal shelf with photograph, pen, borscht sachet. |
| ZENITH     | Air vent, reading light (dead). Bunk status panel.               |
| NADIR      | Storage netting. Dirty laundry, a second borscht sachet, a deck of cards. |

### 3. Reactor Module (new)

Aft of Crew Quarters. Nuclear power unit — RORSAT-lineage design. Hot.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| FORE       | **Hatch → Crew Quarters** (gated by radiation — requires dosimeter) |
| AFT        | Main engine bell + propellant control valves                      |
| PORT       | Coolant pumps + control panels (essential for a burn)              |
| STARBOARD  | **Hatch → Progress** ferry                                         |
| ZENITH     | Reactor shielding access, warning placards in three languages     |
| NADIR      | Spent-fuel storage (classified, sealed)                           |

Ambient radiation is low but nonzero. Time spent in the module adds to your
cumulative dose. Lethal at ~6 Sv. Dosimeter (found in Life Support) is
required to even enter — without it, the game refuses because you'd die of
radiation poisoning long before you saw the cannon.

### 4. Command Module (existing)

Fore of the Node. Station operations.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| FORE       | External observation port, navigational radar displays (dead before power) |
| AFT        | **Hatch → Central Node**                                          |
| PORT       | Communications array (long-range radio)                           |
| STARBOARD  | **Hatch → Soyuz** ferry                                           |
| ZENITH     | Classified armament safe (the keypad + placard; behind the safe: cannon fire-control) |
| NADIR      | Main workstation, manual pressure gauges, emergency toolkit (has the multimeter) |

Note: the armament CONTROL panel is here in Command (the safe), but the actual
weapons bay is east of the Node. Two locations, one system.

### 5. Soyuz Ferry (docked, starboard of Command)

Three-couch escape craft. Smaller; treated as a room but with minimal exploration.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| FORE       | **Docking ring → Command Module**                                 |
| AFT        | Main engine + maneuvering thrusters                               |
| PORT       | Commander's couch                                                 |
| STARBOARD  | Flight engineer's couch                                           |
| ZENITH     | Research cosmonaut's couch                                        |
| NADIR      | Supply locker, emergency survival kit                             |

Escape ending: you can de-orbit in Soyuz. It alone cannot reach Selengrad
(the math in Yevgenia's notebook is clear). De-orbit = coming home to a
burning planet. A dark ending, but narratively coherent.

### 6. Observation Cupola (existing)

Nadir of the Node. Earth-facing glass blister. Petrov's body is here.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| ZENITH     | **Hatch → Central Node**. Petrov's body pinned near it.            |
| NADIR      | The main viewport (the WWIII reveal)                              |
| FORE       | Side viewport panel, thermal stress instruments                   |
| AFT        | Side viewport panel, emergency curtain (rolled)                   |
| PORT       | Side viewport panel                                               |
| STARBOARD  | Side viewport panel                                               |

### 7. Life Support Module (new)

Zenith of the Node. Atmosphere, water, sensor systems.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| NADIR      | **Hatch → Central Node**                                          |
| FORE       | O₂ generator + LiOH (lithium hydroxide) canister rack              |
| AFT        | Water recycler (gray + black loops)                               |
| PORT       | CO₂ scrubbers (powered down post-EMP; LiOH passive is keeping you alive) |
| STARBOARD  | **Dosimeter panel + radiation sensors** (the dosimeter you need)    |
| ZENITH     | Emergency EVA airlock (sealed, unused in the prototype)            |

### 8. Hydroponics Lab (new)

Port of the Node. Plant growth + research. Quiet cultural echo of Selengrad's
closed-loop atmosphere.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| STARBOARD  | **Hatch → Central Node**                                          |
| FORE       | Growing racks: tomatoes, dill, onion (Soviet real-Mir crop list)   |
| AFT        | Growing racks: wheat, sugar beets, beans                          |
| PORT       | Grow lights (dead). Rescue-seed vault. Unlabeled experimental trays. |
| ZENITH     | Nutrient solution tanks + pumps                                    |
| NADIR      | Trash compactor with compostable plant waste                      |

The plants are starting to freeze — you can examine them as a marker of how
long you've had before the station's temperature drop becomes fatal.

### 9. Armament Bay (new)

Starboard of the Node. The classified armament. Sealed until Petrov's log
is read.

| Face       | What's there                                                     |
|------------|------------------------------------------------------------------|
| PORT       | **Hatch → Central Node** (initially sealed — unlocked via safe in Command) |
| FORE       | The **Rikhter R-23** cannon itself, pointed forward through an armored port in the hull |
| AFT        | Ammunition rack: three 23mm shells, a maintenance kit             |
| STARBOARD  | **Fire-control console**: targeting radar, aim vector, trigger      |
| ZENITH     | Optical periscope (manual backup targeting)                        |
| NADIR      | Armored blast shielding, spare cannon barrel                       |

### 10. Progress Ferry (docked, starboard of Reactor)

Cargo ferry. Minimal treatment — accessible from the Reactor module but not
a full 6-face room; it's a supply cache you reach into.

Contains: additional water, food sachets, a spare multimeter, a pressurized
tool kit, an untampered medical dose of potassium iodide (radiation
prophylaxis — useful for Reactor entry).

## Starting state + gating

| Module        | Start state                    | Unlocks via                                    |
|---------------|--------------------------------|------------------------------------------------|
| Crew Quarters | Accessible (you wake here)     | —                                              |
| Central Node  | Vacuum (hatches sealed)        | Pressure valve in Crew Quarters                |
| Command       | Accessible post-Node           | —                                              |
| Cupola        | Accessible post-Node           | —                                              |
| Life Support  | Accessible post-Node           | —                                              |
| Hydroponics   | Accessible post-Node           | —                                              |
| Armament Bay  | Sealed                         | Open safe in Command w/ Petrov's log code      |
| Reactor       | Refused by narrator (lethal)   | Take the dosimeter from Life Support (+ optionally the potassium iodide from Progress) |
| Soyuz         | Accessible from Command        | —                                              |
| Progress      | Accessible from Reactor        | Reactor clearance (dosimeter)                  |

## Within a module: 6-face interaction

Each face's feature is part of the module's room description. Players don't
have to learn "nadir" or "starboard" to interact — but they CAN use those
words, and the dedicated directional commands (UP, DOWN, etc.) move them to
the adjacent module.

Example Life Support description:

> **Life Support Module**
>
> A cylindrical compartment painted the institutional green of Soviet
> spaceflight. Every inner surface is equipment.
>
> Forward, the **O₂ generator** stands silent — a stack of lithium-hydroxide
> canisters ticks passively beneath it. Aft, the **water recycler** drips
> condensate into a catch-tray. On the port wall, **CO₂ scrubbers** hang
> dark, their fans stopped by the EMP. On the starboard wall, a
> **dosimeter panel** glows faintly; evidently it has its own power cell,
> because nothing else should be running. Overhead, an emergency EVA
> airlock is dogged shut.
>
> The hatch to Central Node is below you.

The player can then `EXAMINE O2 GENERATOR`, `TAKE DOSIMETER`, `EXAMINE
DOSIMETER PANEL`, `DOWN`, etc.

## Showing the player a map

**In-story MAP command**. New action. Prints a simple textual schematic:

```
> MAP

  Mir-3 Orbital Station — Schematic
  ─────────────────────────────────
                    [Life Support]
                         │ UP
        [Hydroponics] ←— NODE —→ [Armament Bay]  ✪
                         │ DOWN
                    [Observation Cupola]

        [Crew Quarters] ←—————— NODE ——————→ [Command Module]
              │ AFT                                │ E
        [Reactor ☢]                            [Soyuz]
              │ STARBOARD
        [Progress ⎯]

  You are in the Central Node.
  ✪ classified · ☢ radiation hazard · ⎯ docked ferry
```

Modules you haven't entered yet are shown as `[???]`. The player builds up
knowledge of the station as they explore.

**Sidebar display**. The current ASCII "scene art" panel continues to show
each room's interior when you're in it. A new **MAP** toggle (or a second
panel below the scene) could show a miniature of the station schematic. I'd
defer that to a later pass — the text MAP command is the minimum useful
feature.

## Implementation order (proposed)

1. Define the 6-direction grammar in `story.ni` (add UP/DOWN, keep N/S/E/W)
2. Re-model the four existing rooms as modules with 6-face descriptions
3. Add `MAP` action printing the schematic
4. Add the six new modules (Reactor, Life Support, Hydroponics, Armament
   Bay, Soyuz, Progress), one per scene, each with its 6-face description
5. Wire gating (dosimeter for Reactor, safe-code for Armament Bay)
6. Extend the in-sidebar scene art to cover new modules (new ASCII images)
7. Playtest the navigation and adjust descriptions

Each step is a commit. Expect steps 1–3 to be ~half a day; steps 4–5 about
a day; step 6 is flavor and can trail.

## Open questions before I build

1. **Direction naming in the parser**: stick with N/S/E/W/U/D (familiar,
   short), or accept FORE/AFT/PORT/STARBOARD as synonyms? I'd add both —
   everyone benefits.
2. **MAP verbosity**: the full schematic every time, or progressive
   reveal (only modules you've entered)?
3. **Starting point**: keep the player in Crew Quarters, or move them to
   a bunk in the **Crew Quarters PORT wall** (more faithful to zero-g
   bunk-in-a-slot)?
4. **Cannon scope for this pass**: just open the Bay hatch (keep cannon
   non-functional as in the current safe mechanic), or fully wire it
   (aim + fire + ASAT target) in the same PR?

Answers to these drive scope. Once you pick, I'll execute.
