# Wave 1 Shared-State Contract

Three features (#14 title/menu, #15 save/load, #16 intro) are being built in parallel on top of `game/ui.js`. This document defines their shared boundaries so they don't conflict.

## App Lifecycle Phases

Add `gamePhase` to the existing `state` object in `ui.js`:

```
TITLE → INTRO → PLAYING → PAUSED
```

| Phase    | Owner       | Input handling                          |
|----------|-------------|-----------------------------------------|
| TITLE    | #14 menu    | Menu navigation only (arrow keys, Enter)|
| INTRO    | #16 intro   | Any key / click to skip                 |
| PLAYING  | existing UI | Commands go to interpreter              |
| PAUSED   | #14 menu    | Menu navigation (ESC toggles pause)     |

**Rule**: Only the phase owner processes input. `handleKeyDown()` in `ui.js` must check `state.gamePhase` first and delegate accordingly.

## State Additions

Each feature adds to the existing `state` object (don't replace it):

```javascript
// #14 adds:
state.gamePhase = "TITLE"    // enum: TITLE | INTRO | PLAYING | PAUSED
state.menuVisible = false     // true when pause menu overlay is shown

// #15 adds:
state.saveSlots = []          // array of { slot: number, timestamp: string, room: string }

// #16 adds:
state.introComplete = false   // set true after intro finishes or is skipped
```

## Public API Extensions

Extend `window.MirsEnd` (don't replace existing methods):

```javascript
// #14 adds:
MirsEnd.setPhase(phase)       // transition gamePhase, update UI visibility
MirsEnd.showMenu()            // show pause overlay, set phase PAUSED
MirsEnd.hideMenu()            // hide overlay, set phase PLAYING

// #15 adds:
MirsEnd.saveGame(slot)        // serialize state + interpreter to localStorage
MirsEnd.loadGame(slot)        // deserialize and restore
MirsEnd.listSaves()           // return saveSlots array
MirsEnd.autoSave()            // called on room transitions

// #16 adds:
MirsEnd.playIntro()           // start intro sequence
MirsEnd.skipIntro()           // jump to PLAYING phase
```

## DOM Conventions

- **Menu overlay**: `#menu-overlay` div, absolutely positioned over game content. Hidden by default.
- **Intro container**: `#intro-container` div, replaces/overlays `#story-output` during INTRO phase.
- **Save UI**: Part of the menu overlay (save/load as menu sub-screens), not a separate DOM layer.

All new DOM elements go inside the existing `#game-container`. No new top-level elements.

## Init Sequence

```
1. DOM ready
2. #14: show title screen (gamePhase = TITLE)
3. User selects "New Game" → #16: playIntro() → gamePhase = INTRO
   User selects "Continue" → #15: loadGame(mostRecent) → gamePhase = PLAYING
4. Intro completes or skipped → gamePhase = PLAYING
5. Existing ui.js init: hookInterpreter(), start game
```

## Save Format

localStorage key: `mirsend-save-{slot}` (slot 1-3, slot 0 = autosave)

```json
{
  "version": 1,
  "timestamp": "ISO-8601",
  "state": { "currentRoom": "...", "o2": 100, "morale": 70, "inventory": [] },
  "commandHistory": ["look", "north", "..."],
  "interpreterSnapshot": "base64-encoded Glulx save data (if available)"
}
```

## ESC Key Behavior

- TITLE: no-op
- INTRO: skip intro → PLAYING
- PLAYING: open menu → PAUSED
- PAUSED: close menu → PLAYING

## File Organization

Each feature adds files under `game/`:
- `game/menu.js` (#14)
- `game/save.js` (#15)
- `game/intro.js` (#16)

These are loaded by `play.html` after `ui.js` and register themselves via `window.MirsEnd`.
