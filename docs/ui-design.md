# UI Design — Soviet Terminal Visual Language

The visual language for MIR'S END. The world is an alternate-timeline late-80s/early-90s Soviet space station; the interface is the player's onboard computer terminal. Authoritative reference: the mockups under `game/mockups/`. Until issue #132 lands, those files are the ground truth — this doc describes the rules they encode.

| Mockup | Purpose |
|---|---|
| `v3-textmode.html` | Text-mode terminal (story + sidebar + status). The default game state. |
| `v4-video.html` | Full-screen ASCII video playback. |
| `v5-cutscene.html` | Terminal ↔ video transition (per-column wipe). |

Screenshots: [`docs/ui-mockups/`](ui-mockups/)

## Layout

- **Resolution:** 80 columns × 25 rows. Period-correct for late-80s Soviet/DEC/IBM terminals (DVK, ИЭ-15, VT220, IBM 3270 all standardized on this grid).
- **Body split:** story column 48 chars, sidebar 25 chars, separated by a vertical divider. With borders + padding, total = 80 (`║ + 1 + 48 + 1 + │ + 1 + 25 + 1 + ║`).
- **Bezel chrome:** painted-metal frame around the screen with corner screws, etched ID plate above, vent slots + brand stamp + power LED below. Bezel always visible — the screen content changes; the hardware does not.

## Typography

- **Font:** **IBM Plex Mono** (true monospace, full Cyrillic, free).
- **Weights used:** 400 (default), 500 (medium / headings), 600 (ID plate stamping).
- **No ligatures** — disable via `font-feature-settings: "liga" 0, "calt" 0`.
- **Fallbacks:** `'Cascadia Mono', 'DejaVu Sans Mono', 'Consolas', monospace` — these have full box-drawing + geometric shape coverage in case Plex Mono lacks a glyph.

## Color palette

| Token | Hex | Use |
|---|---|---|
| `--screen-bg` | `#0a1408` | Phosphor screen background |
| `--screen-bg-deep` | `#050a04` | Vignette outer color |
| `--phosphor` | `#6cf06b` | Default phosphor green (P1) |
| `--phosphor-dim` | `#3a8a39` | Dim text, borders, secondary content |
| `--phosphor-bright` | `#b6ffb5` | Highlight, headings, cursor |
| `--lamp-red` | `#ff4530` | Annunciator: danger / fault |
| `--lamp-amber` | `#ffb020` | Annunciator: warning |
| `--lamp-green` | `#4dff60` | Annunciator: ok / nominal |
| `--lamp-white` | `#f0f5e8` | Annunciator: info / docked |
| `--lamp-off` | `#1a2418` | Annunciator: disabled / unpowered |
| `--bezel-paint` | `#6b7560` | Painted olive-grey terminal enclosure |
| `--bezel-paint-shadow` | `#3f4639` | Bezel shadow / etched plate engraving |
| `--label-cream` | `#d8d2bc` | Etched plate background |

## Inline color tier tags

Inside the screen `<pre>` we use custom tags (styled by tag selector in CSS) to color runs of glyphs. They are zero-effort to write and visually terse in the source.

| Tag | Color | Typical use |
|---|---|---|
| `<bri>` | bright phosphor | values, highlights, cursor, leading edge of wipes |
| `<dim>` | dim phosphor | dividers, inactive labels, echo'd commands' tail |
| `<hd>` | bright + medium weight | section titles (`VITALS / СОСТОЯНИЕ`) |
| `<echo>` | dim phosphor | player commands echoed into output (`> examine logbook`) |
| `<cur>` | bright + glow + blink | the input cursor (`█`) |
| `<grn>` `<amb>` `<red>` `<wht>` `<off>` | lamp colors | annunciator glyphs |

When updating padding helpers, account for tags: `visLen()` strips both `<...>` tags **and** HTML entities (`&gt;` → 1 char) before counting.

## Bilingual labels

Headings and ID plate fields appear in both Latin and Cyrillic to reinforce alt-timeline:

```
VITALS / СОСТОЯНИЕ
SYSTEMS / СИСТЕМЫ
INVENTORY / ИНВЕНТАРЬ
COMMAND MODULE / КОМАНДНЫЙ МОДУЛЬ
```

The Cyrillic is **real Russian**, not faux-Cyrillic letter substitution. Faux-Cyrillic was explicitly rejected — it reads as kitsch and signals "American who can't read Russian." Real labels signal "this is bilingual hardware."

## Glyph standards

| Use | Glyph | Notes |
|---|---|---|
| Annunciator lamp | `█` (U+2588 FULL BLOCK) | Originally `■` but it's missing from Plex Mono → fallback to a proportional font and broke alignment |
| Inventory bullet | `>` | Originally `▸` but same fallback problem |
| Bar gauge — lit | `█` | |
| Bar gauge — unlit | `░` (U+2591 LIGHT SHADE) | |
| Cursor | `█` blinking | |
| Box-drawing — heavy | `╔ ═ ╗ ║ ╚ ╝ ╠ ╣` | Outer screen frame |
| Box-drawing — light | `┌ ─ ┐ │ └ ┘ ├ ┤` | Reserved for inner panels (not used yet) |
| Junction (heavy ↔ light) | `╤ ╧` | Top/bottom of the story↔sidebar divider |
| Multiplication | `x` (lowercase Latin) | NOT `×` (U+00D7) — keeps source plain |

## Brightness ramps (for ASCII video)

- Default 11-step ramp: `' .:;-=+*#%@'` — dark to light.
- `--tiers=3` in the converter wraps the ramp in `<dim>` (` .:;`) / default (`-=+`) / `<bri>` (`*#%@`) for 3 levels of phosphor brightness in playback.

## Animation conventions

| Effect | Where | Notes |
|---|---|---|
| Static scanlines | overlay on `#screen` | `repeating-linear-gradient`, ~3px stripe at 20% opacity |
| Vignette | overlay on `#screen` | radial dark fade at edges |
| Sweeping scanline | bright band that travels top→bottom | random duration (0.9–4.2s), random opacity (0.35–1.0), random gap (2.5–9s, occasional rapid double-sweep) |
| Cursor blink | `<cur>█</cur>` | 1.05s steps |
| Cutscene wipe | per-column, terminal ↔ video | random per-column delay (0–55% of total) and duration (35–60% of total). Bright leading char + dim trailing char on the head |
| Phosphor jitter | brief brightness blip | 8s loop, brief blip at 47–50%, very subtle |

All animations should be gated by `prefers-reduced-motion: reduce` (see issue #144). The static scanlines and vignette stay; everything else degrades to a hard cut.

## Hardware details

The bezel renders olive-grey painted metal with corner screws, an etched ID plate stamped with `МИР-2 / MIR-2 STATION · ОРБИТАЛЬНАЯ СТАНЦИЯ`, vent slots, a red power LED labeled `PWR / ПИТ`, and a brand stamp `ЭЛЕКТРОНИКА · МС-0511 · 1989` modeled on the real Soviet Elektronika brand line. Model number, console number, and operator name on the ID plate can be game-state-driven (e.g. `OP. KOVAL, A.I.` reflects the player character).
