# Integration Tests

This directory contains the automated test suite that gates the project
milestones. Each milestone has its own integration test file that must pass
before the next milestone can be considered started.

| Milestone | File | Issue |
|---|---|---|
| M1: Inform 7 Foundation | `test_m1_integration.py` | #17 |
| M2: Playable Prototype | _pending_ | #18 |
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

## Manual smoke checks

A few things are not worth automating but should be eyeballed before tagging
a milestone complete:

- **Browser playback** — open `game/play.html` after building and confirm the
  Quixe/Parchment interpreter loads `story.ulx` without errors.
- **Output legibility** — start the story in a terminal and read through the
  opening sequence. The automated tests confirm the parser responds, but a
  human still needs to spot awkward phrasing or missing punctuation.

## Adding tests for a new milestone

1. Create `tests/test_m{N}_integration.py`.
2. Mirror the structure: build pipeline, runtime behavior, regression.
3. Use the same `needs_compiler` / `needs_glulxe` skip markers from
   `test_m1_integration.py` so the suite stays runnable in degraded
   environments.
4. Update the table at the top of this file.
5. Link to the milestone issue (`#18`, `#19`, …).
