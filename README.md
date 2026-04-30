# MIR'S END

An illustrated text adventure built with [Inform 7](http://inform7.com/) targeting the [Glulx](https://www.eblong.com/zarf/glulx/) virtual machine for browser-based play.

## Prerequisites

- Node.js >= 18
- Inform 7 compiler (v10.1.2, from the macOS IDE — see below)

### Installing Inform 7

We pin to the **stable v10.1.2** compiler from the [TobyLobster Inform macOS IDE](https://github.com/TobyLobster/Inform/releases). The `ganelson/inform` master branch (v10.2.0 experimental) is non-deterministically broken — it produces corrupt Glulx binaries from the same source across repeated runs — so we avoid it.

```bash
# 1. Download the latest Inform.app DMG
#    https://github.com/TobyLobster/Inform/releases
open ~/Downloads/inform_10_1_2_macOS_*.dmg

# 2. Copy the compiler binaries + Internal resources
mkdir -p $HOME/Code/inform-stable
cp /Volumes/Inform/Inform.app/Contents/MacOS/ni        $HOME/Code/inform-stable/
cp /Volumes/Inform/Inform.app/Contents/MacOS/inform6   $HOME/Code/inform-stable/
cp -R /Volumes/Inform/Inform.app/Contents/Resources/Internal $HOME/Code/inform-stable/

# 3. Unmount
hdiutil detach /Volumes/Inform
```

If your install path differs, set `INFORM7_STABLE_HOME`:
```bash
export INFORM7_STABLE_HOME=/custom/path/to/inform-stable
```

The `scripts/compile-inform7.sh` script runs `ni` (I7 → I6) then `inform6` (I6 → Glulx) directly.

## Setup

```bash
npm install
```

## Build

### Compile the story

Compiles the Inform 7 source (`game/inform/Source/story.ni`) to a Glulx story file (`game/dist/story.ulx`):

```bash
npm run build:story
```

The build script checks for the compiler via `INFORM7_COMPILER` env var or `inform7` on PATH.

### Compile TypeScript

```bash
npm run build:ts
```

### Build everything

```bash
npm run build
```

## Playing in a Browser

The compiled `.ulx` story file can be played in browser-based Glulx interpreters:

1. **Build the story**: `npm run build:story`
2. **Choose an interpreter**:
   - [Quixe](https://eblong.com/zarf/glulx/quixe/) — JavaScript Glulx interpreter
   - [Parchment](https://github.com/curiousdannii/parchment) — multi-format IF interpreter
3. **Open `game/play.html`** in your browser (after placing interpreter files in `game/lib/`)

Alternatively, upload `game/dist/story.ulx` to the [Parchment web player](https://iplayif.com/).

## Project Structure

- `game/inform/Source/story.ni` — Inform 7 source file
- `game/inform/Build/` — Intermediate build artifacts (git-ignored)
- `game/dist/` — Compiled output (git-ignored)
- `game/dist/story.ulx` — Compiled Glulx story file
- `game/play.html` — Browser-based play page (requires interpreter)
- `game/story/` — Ink story source files (kept as reference during narrative port)
- `game/src/` — TypeScript game source
- `game/assets/` — Game assets (ASCII art, etc.)
- `scripts/compile-inform7.sh` — Build script for Inform 7 compilation
- `world/` — World design documents
- `generation/` — Content generation tooling

## Inform 7 Compilation

This project uses the open-source [Inform 7 compiler](https://github.com/ganelson/inform) to compile natural-language source code to Glulx bytecode. The compilation pipeline is:

```
story.ni (Inform 7 source)
  → inform7 compiler
    → story.ulx (Glulx bytecode)
      → Quixe/Parchment (browser interpreter)
```

The build script (`scripts/compile-inform7.sh`) handles compiler detection, compilation, and output file placement.

## CI

GitHub Actions runs on every push to `main` and on every pull request targeting `main`. The workflow (`.github/workflows/ci.yml`) runs:

- **Lint** — `npx biome check .`
- **TypeScript** — `npm run build:ts`
- **Node tests** — `npm test` (story validation)
- **Python tests** — `pytest tests/` (project structure, assets, UI, Inform 7 source validation)

The Inform 7 compiler is not available in CI, so toolchain-dependent tests skip automatically when `inbuild` is missing.

## Migration from Ink

This project is migrating from Ink to Inform 7. The original Ink files are kept in `game/story/` as reference until the narrative port is complete. The Ink compilation script remains at `scripts/compile-ink.mjs` for reference.

