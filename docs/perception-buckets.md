# Perception Buckets

The perception overlay (see `game/ui.js` and `game/perceptions.json`) selects variant text by mapping the player's current morale to one of three buckets. Thresholds match the morale color thresholds the sidebar already uses, so the visual register and the prose register stay in sync.

| Bucket        | Morale range | Sidebar color |
| ------------- | ------------ | ------------- |
| `morale:low`  | 0 to 25      | red           |
| `morale:mid`  | 26 to 50     | amber         |
| `morale:high` | 51 to 100    | bright        |

Starting morale is 70, so the player begins in `morale:high`. Crossing into `morale:mid` happens after meaningful losses (the Yevgenia look, the war reveal). `morale:low` is reserved for sustained breakdown.

Only morale is a bucket axis today. O2 is rendered in the sidebar but does not bucket prose. Dose is not yet tracked as player state and will plug in here when wired (issue #41 notes this is future work).

Bucketing is re-evaluated per turn from the latest `MIRSEND` status line. Re-examines roll fresh, so a morale crash mid-look reads at the new register on the next attempt.
