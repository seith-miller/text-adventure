# M10 playtest — Argon-87 grammar (flag OFF)

**Date:** 2026-05-04
**Branch:** feature/m10-docs-and-qa
**Story version:** 0.1.0+043de64-dirty (Release 1 / Serial 260504)
**Driver:** MCP server via Claude Code; flag-OFF path (canned line)
**Session id:** 2e6b5e0c5795

## What this exercises

The story.ni change in M10 / #101 added `ask argon` and `ask station ai`
(no-topic) to the *talking-to-argon* understand line so the canned-line UX
fires for those phrasings. This run sanity-checks all six command shapes
plus a non-AI gameplay slice to confirm no regression in the rest of the
parser.

## Verb coverage (all return the canned line)

| Command | Result |
|---|---|
| `ask argon` | "The AI channel is dead. Argon-87's console is dark." |
| `ask argon about systems` | (same canned line — pre-existing grammar still routes through ui.js intercept) |
| `talk to argon` | (same) |
| `speak to argon` | (same) |
| `ask station ai about reactor` | (same) |
| `ask station ai` | (same — new no-topic alias added in this milestone) |
| `ask argon about kozlova` (after room change) | (same) |

All six print the canned line cleanly. No "I didn't understand" parser
errors; no double-print; no console errors.

## Non-AI gameplay slice (regression check)

| Turn | Command | Result |
|---|---|---|
| 7 | `take pen` | Taken. |
| 8 | `go forward` | Soft-blocked: "should find a light source first" (correct — flashlight not yet active). |
| 9 | `open locker` | Reveals flashlight; +1 score. |
| 10 | `take flashlight` | Taken. |
| 11 | `light flashlight` | "...beetle-drone... warm yellow beam..." (in-voice prose). +1 score. Morale ticks up. |
| 12 | `go forward` | Soft-blocked: corridor vented, valve still closed. (Correct.) |
| 13 | `open valve` | Pressure-equalize prose. +1 score. |
| 14 | `go forward` | Enters Main Corridor. Yevgenia present. |

Room transition Crew Quarters → Main Corridor works. Score increments fire.
Auto-save triggers on room change. No regressions.

## Final state

- Room: Main Corridor
- O2: 65 (started at 100; 35-turn natural decay including the valve event)
- Morale: 59
- Inventory: flashlight, pen
- Score: 3

## Notes for future-us

- The `inventory` field surfaced via MCP includes a debug status-line
  fragment ("b1=0 b2=0 act2=none") appended to the last item. Pre-existing
  parsing artifact in [scripts/mirs_end_mcp.py](../../scripts/mirs_end_mcp.py),
  not related to this milestone. Worth a follow-up filing.
- Did not exercise the warm AI path (flag-ON + live proxy) in this run;
  that path is now covered by `scripts/qa-voice-drift.py` (#69) under a
  budget gate, and by the Playwright `ai-feature-flag` suite for offline
  guarantees.
