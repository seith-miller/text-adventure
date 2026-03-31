# Text Adventure

An illustrated text adventure built with [Ink](https://www.inklestudios.com/ink/) and [inkjs](https://github.com/y-lohse/inkjs).

## Prerequisites

- Node.js >= 18

## Setup

```bash
npm install
```

## Build

Compile Ink stories to JSON:

```bash
npm run build:story
```

Compile TypeScript:

```bash
npm run build:ts
```

Build everything (stories + TypeScript):

```bash
npm run build
```

## Project Structure

- `game/story/` — Ink story source files (`.ink`)
- `game/src/` — TypeScript game source
- `game/dist/` — Compiled output (git-ignored)
- `game/dist/story/` — Compiled story JSON files
- `game/assets/` — Game assets
- `world/` — World design documents
- `generation/` — Content generation tooling

## Ink Compilation

This project uses **inkjs's built-in compiler** rather than the native `inklecate` tool. This keeps the toolchain as pure Node.js, avoiding a dependency on Mono/.NET and making setup simpler across platforms.
