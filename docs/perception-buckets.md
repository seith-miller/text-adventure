# Perception Buckets

The perception overlay (see `game/ui.js` and `game/perceptions.json`) selects variant text by mapping the player's current morale to one of three buckets. Thresholds match the morale color thresholds the sidebar already uses, so the visual register and the prose register stay in sync.

| Bucket        | Morale range | Sidebar color |
| ------------- | ------------ | ------------- |
| `morale:low`  | 0 to 25      | red           |
| `morale:mid`  | 26 to 50     | amber         |
| `morale:high` | 51 to 100    | bright        |

Starting morale is randomized between 30 and 55 per playthrough (`game/inform/Source/story.ni`, "now morale-level is a random number between 30 and 55"). About 60% of openings land the player in `morale:mid`; the remainder land in `morale:low`. The `morale:high` register is the *minority* first-play experience and is earned through gains (the Zhuchok flashlight, food, rest) rather than starting state.

The `ui.js` default of 70 only displays before the first MIRSEND status line arrives; the next turn replaces it with the Inform 7 value. Player-facing prose is keyed off the post-MIRSEND value, so the 70 default never determines a perception bucket.

`morale:low` deepens further after the war reveal (`-15`) and from sustained reactor occupancy (`-1` per turn).

Only morale is a bucket axis today. O2 is rendered in the sidebar but does not bucket prose. Dose is not yet tracked as player state and will plug in here when wired (issue #41 notes this is future work).

Bucketing is re-evaluated per turn from the latest `MIRSEND` status line. Re-examines roll fresh, so a morale crash mid-look reads at the new register on the next attempt.
