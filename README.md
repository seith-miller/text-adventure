# MIR'S END

An illustrated text adventure built with [Inform 7](http://inform7.com/) targeting the [Glulx](https://www.eblong.com/zarf/glulx/) virtual machine for browser-based play.

## Prerequisites

- Node.js >= 18
- Inform 7 compiler (built from source)

### Installing Inform 7

There is no package manager formula — the compiler must be built from source. All three repos must be siblings in a shared parent directory:

```bash
mkdir inform7-build && cd inform7-build

# 1. Build inweb (build tool, no dependencies)
git clone https://github.com/ganelson/inweb.git
bash inweb/scripts/first.sh macosarm    # use 'macos' for Intel, 'linux' for Linux

# 2. Build intest (test tool, depends on inweb)
git clone https://github.com/ganelson/intest.git
bash intest/scripts/first.sh

# 3. Build inform (the compiler, depends on both)
git clone https://github.com/ganelson/inform.git
cd inform
bash scripts/first.sh
```

The compiler binary will be at `inform/inform7/Tangled/inform7`.

**Configure for this project** — either:
- Add the binary to your PATH, or
- Set the `INFORM7_COMPILER` environment variable:
  ```bash
  export INFORM7_COMPILER=/path/to/inform7-build/inform/inform7/Tangled/inform7
  ```

The build script will auto-detect the Internal resources directory relative to the compiler binary.

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
