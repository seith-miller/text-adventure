# MIR'S END

An illustrated text adventure built with [Inform 7](http://inform7.com/) targeting the [Glulx](https://www.eblong.com/zarf/glulx/) virtual machine for browser-based play.

## Prerequisites

- Node.js >= 18
- Inform 7 compiler (one of the following):
  - **CLI**: Install from [ganelson/inform](https://github.com/ganelson/inform)
    - macOS: `brew install inform7`
    - Linux: build from source (see below)
  - **Docker**: `docker pull ganelson/inform7`

### Installing Inform 7 from Source (Linux)

```bash
git clone https://github.com/ganelson/inform.git
cd inform
make
sudo make install
```

This installs the `inform7` CLI tool, which compiles `.ni` (Inform 7) source files to Glulx (`.ulx`) or Z-machine (`.z8`) story files.

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

The build script automatically detects available compilers in this order:
1. `inform7` CLI (native)
2. `ni` CLI (alternative name)
3. Docker-based compilation

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

## Migration from Ink

This project is migrating from Ink to Inform 7. The original Ink files are kept in `game/story/` as reference until the narrative port is complete. The Ink compilation script remains at `scripts/compile-ink.mjs` for reference.
