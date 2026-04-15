# Integration Tests

This directory contains the automated test suite that gates the project
milestones. Each milestone has its own integration test file that must pass
before the next milestone can be considered started.

| Milestone | Files | Issue |
|---|---|---|
| M1: Inform 7 Foundation | `test_m1_integration.py` | #17 |
| M2: Playable Prototype | `test_m2_inform7_game.py`, `test_m2_web_ui.py`, `test_m2_integration.py` | #18 |
| M3: Complete Experience | _pending_ | #19 |

## Running the suite

The Python tests use a project-local virtualenv at `.venv/`.

```bash
# One-time setup
python3 -m venv .venv
.venv/bin/pip install pytest

# Run everything
.venv/bin/pytest tests/

# Run only the M1 milestone gate
.venv/bin/pytest tests/test_m1_integration.py -v

# Run only the M2 milestone gate
.venv/bin/pytest tests/test_m2_inform7_game.py tests/test_m2_web_ui.py tests/test_m2_integration.py -v
```

## Required tools

The full suite expects these tools to be available. Tests degrade gracefully
(skip rather than fail) when an optional tool is missing.

| Tool | Required for | Install |
|---|---|---|
| Python 3.12+ | All Python tests | `mise install` (per `.mise.toml`) |
| Node.js 18+ | npm-based regression checks | `mise install` |
| `glulxe` | Interactive story tests in M1 | `brew install glulxe` |
| Inform 7 toolchain (`inbuild`) | Clean rebuild + invalid-source tests | Build from source — see [README.md](../README.md) |

When a required tool is missing, the affected tests are skipped with a
clear `reason=` so you know what you are not exercising.

## Driving the Glulx interpreter from tests

The Homebrew build of `glulxe` links against `glktermw`, a curses-based GLK
implementation that requires a real TTY. Piping commands directly into stdin
fails with `Error opening terminal: unknown.` because there is no controlling
terminal.

`tests/glulxe_driver.py` works around this by spawning glulxe inside a
pseudo-terminal via `pty.fork()`, writing the inputs into the master side,
draining the output until the child exits, and then stripping the curses
escape sequences so tests can make plain-text assertions.

A few quirks worth knowing:

- glktermw eats the **first character of the first command** because it shows
  a "press any key" prompt at the title screen. The driver prepends a leading
  newline to absorb it. Don't try to send commands without that warmup.
- The `quit` verb prompts `Are you sure you want to quit?` — the driver
  appends `y\n` after every input list so the interpreter exits cleanly.
- Output contains both the issued commands and the parser responses, plus a
  good amount of curses positioning whitespace. Use `glulxe_driver.normalize()`
  for assertions; it strips ANSI codes and collapses whitespace.

## What M1 verifies (`test_m1_integration.py`)

The M1 gate has three sections:

### Build pipeline
- The compile script exists and is executable.
- The Inform 7 source declares the game title.
- A compiled `.ulx` exists in `game/dist/`.
- The compiled file starts with the Glulx magic number `Glul`.
- The compiled file is at least 200 KB (a sentinel against stub builds).
- A clean rebuild (with `Build/` and `dist/` removed) succeeds. *Skipped when
  the Inform 7 toolchain is missing.*
- The compile script returns non-zero on malformed Inform 7 source.
  *Skipped when the toolchain is missing; restores the original source on
  exit so other tests are not poisoned.*

### Story behavior
*All require `glulxe`.*

- Launching the story shows the title screen and the Crew Quarters room.
- `LOOK` reprints the current room description.
- `OPEN EMERGENCY LOCKER` followed by `EXAMINE EMERGENCY LOCKER` reveals the
  chemical flashlight inside.
- `N` (north) navigates to the Main Corridor.
- `QUIT` produces the standard confirmation prompt and exits cleanly.

### Regression
- `package.json` still wires `npm run build:story` to the Inform 7 script.
- `npx biome check .` passes (lint regression of CI workflow #6).
- `node_modules` exists and `inkjs` is still installed (regression of #3).

## What M2 verifies

M2 testing is split across three files:

### `test_m2_inform7_game.py`
Inform 7 game completeness: all rooms reachable via standard directions,
object interactivity (EXAMINE/TAKE/OPEN/USE), NPC conversations (Yevgenia
and Petrov topics), full story progression (darkness → corridor → cupola →
command module → radio → distress call → Moon plan), oxygen/morale tracking,
and parser responses for common verbs in each room.

### `test_m2_web_ui.py`
Web UI shell: text panel (story output, player input echo, auto-scroll),
scene art panel (room-to-art mapping, fetch/cache, room change detection),
status panel (O2/morale bars with color thresholds, inventory), text input
(Enter to send, ArrowUp/Down history), Hitchhiker's-style layout, dark theme,
and interpreter integration (GlkOte, Parchment, fallback shell, public API).

### `test_m2_integration.py`
Cross-component: scene art filenames match Inform 7 room identifiers, status
variables consistent between game and UI, code quality (no console.error /
debugger / alert), biome lint infrastructure, build pipeline (npm scripts,
TypeScript compilation), and full M1 regression suite.

## Manual smoke checks

A few things are not worth automating but should be eyeballed before tagging
a milestone complete:

- **Browser playback** — open `game/play.html` after building and confirm the
  Quixe/Parchment interpreter loads `story.ulx` without errors.
- **Output legibility** — start the story in a terminal and read through the
  opening sequence. The automated tests confirm the parser responds, but a
  human still needs to spot awkward phrasing or missing punctuation.

### M2 browser test procedures

Prerequisite for all browser tests: build the story (`npm run build:story`)
and serve the `game/` directory with a local web server
(`cd game && python3 -m http.server 8080`), then open
`http://localhost:8080/play.html`.

#### Browser compatibility (Chrome / Firefox / Safari)
- Page loads, dark theme visible
- Layout: left text, right sidebar — grid layout matches spec
- Scene art panel shows ASCII art (`[No signal]` or darkness art)
- Status panel shows O2 / Morale / Inventory with values
- Command typed and Enter pressed — input echoed in story panel
- Up arrow recalls previous command; Down arrow steps forward through history

#### Full game playthrough (requires Quixe/Parchment in `game/lib/`)

| Step | Command | Expected |
|---|---|---|
| 1 | *(game starts)* | "You wake to nothing..." |
| 2 | `OPEN LOCKER` | Locker opens, flashlight visible |
| 3 | `TAKE FLASHLIGHT` | Flashlight taken |
| 4 | `SWITCH ON FLASHLIGHT` | Green glow, room description updates |
| 5 | `LISTEN` | Tapping code heard (3-2-3), morale +3 |
| 6 | `NORTH` | Main Corridor; meet Yevgenia and Petrov |
| 7 | `ASK YEVGENIA ABOUT EMP` | Yevgenia describes the pulse |
| 8 | `TALK TO PETROV` | Petrov gives status report |
| 9 | `EAST` | Observation Cupola |
| 10 | `EXAMINE VIEWPORT` | War discovered, morale -15 |
| 11 | `WEST` | Main Corridor |
| 12 | `NORTH` | Command Module |
| 13 | `OPEN TOOLKIT` | Toolkit opens |
| 14 | `TAKE MULTIMETER` | Multimeter taken |
| 15 | `RESTORE POWER` | Power restored, console on, morale +10 |
| 16 | `LISTEN` | Distress call from Freedom Station |
| 17 | `TRANSMIT` | Commander Chen, Selengrad plan, "Begin preparations" |

Alternative at step 17: `STAY SILENT` — Petrov responds, morale -8 instead of +8.

#### Scene art per room
darkness → `darkness.txt`; Crew Quarters → `bunks.txt`; Main Corridor →
`corridor.txt`; Observation Cupola → `earth_from_orbit.txt`; Command Module →
`command_module.txt`.

#### Status panel deltas
Each turn: O2 -1. Switch on flashlight: morale +5. Listen in Crew Quarters
(first time): morale +3. Examine viewport (first time): morale -15. Restore
power: morale +10. Transmit: morale +8. Stay silent: morale -8.

#### Dark theme
Background #0a0c10, text #c8d6e5, scene art #5b9bd5, input #7ec8e3, O2 bar
green→red as it drops, subtle dark scrollbar, no white backgrounds anywhere.

#### Console
No JS errors on load, no errors after commands, no 404s for CSS/JS/art.

## Adding tests for a new milestone

1. Create `tests/test_m{N}_*.py` files (one per concern, following M2's
   pattern, or a single `test_m{N}_integration.py` if simpler like M1).
2. Mirror the structure: build pipeline, runtime behavior, regression.
3. Use the same `needs_compiler` / `needs_glulxe` skip markers from
   `test_m1_integration.py` so the suite stays runnable in degraded
   environments.
4. Update the table at the top of this file.
5. Link to the milestone issue (`#19`, …).
