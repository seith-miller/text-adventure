# The Hidden Cannon — Mir-3's Classified Armament

Historical anchor: Salyut 3 (OPS-2, 1974) carried a Rikhter R-23 23mm
rapid-fire cannon on its forward belly. Test-fired in orbit 24 Jan 1975.
Classified until 1991. Mir-3 inherits that lineage.

## Player-facing capability

A **tool**, not just flavor. The player can:

1. **Discover** the cannon mid-game (post-war-discovered, post-power-
   restored, via an NPC reveal + access panel)
2. **Target** an object in low Earth orbit via the targeting console
3. **Fire** and destroy it — with consequences, not just effects

## Fictional design

- Concealed in an **armament bay** accessed from a stenciled panel in
  the Command Module labeled `КАТАЛОГ ВМФ-07` (fictional military
  cataloging prefix). Before reveal, EXAMINE gives only the stencil;
  the panel reads locked.
- The cannon is the classical Rikhter R-23 — 23mm, rapid-fire, mounted
  rigid to the station (aim = aim the whole station via attitude
  thrusters; ammunition is finite, ~a few hundred rounds historical).
- Targeting is through the **fire-control console** — a second console
  in the Command Module that powers on with `power-is-restored`.

## Gating

| Gate                       | Satisfied by                                          |
|----------------------------|-------------------------------------------------------|
| Know cannon exists         | `cannon-revealed` — set by ASK PETROV ABOUT PANEL or ASK PETROV ABOUT STATION after `war-is-discovered` |
| Access the armament bay    | `cannon-accessible` — Petrov gives a 4-digit arming code; player OPENS CLASSIFIED PANEL |
| Fire control powered       | `power-is-restored`                                   |
| Target acquired            | Player has LISTENed to the fire-control radio at least once (populates threat list) |
| Firing solution            | AIM AT \<target\> — each target has a required condition |

## Target list (minimal ship: one concrete target + two story targets)

### 1. Dead ASAT drone (concrete, gameplay-critical)

A Soviet anti-satellite bus, dormant since pre-war, knocked loose by
the EMP and drifting into a collision course with Mir-3. Radar sweep
reports it at ~45 minutes to impact.

- **If destroyed**: station safe. `asat-destroyed = true`. Morale +5.
- **If ignored past N turns**: station is torn open. Game ends.
- **If wrong target is hit first**: ASAT still inbound; player may
  still try again if ammunition remains.

Makes the cannon *necessary* for reaching the Selengrad burn alive.

### 2. Freedom Station (dark branch — moral option)

The American station. If destroyed, Mir-3 has more delta-v for the
Selengrad burn (less mass to rendezvous with, no need to match
orbits). Three survivors reach the Moon instead of eight.

- Gated behind an explicit AIM AT FREEDOM — parser refuses on
  generic FIRE CANNON if Freedom was the last-aimed target, requiring
  a confirmation (`FIRE CANNON AT FREEDOM`).
- Petrov refuses to help. Yevgenia walks out. Morale −30.
- Story branch: `chen-killed = true` — Selengrad ending text shifts
  to cold-survival beat instead of cooperative-human-species beat.
- Cannot be undone.

### 3. An abandoned American recon satellite (flavor/score)

Legacy Cold War asset still transmitting. Destroying it nets a score
bump and unlocks a stoic Petrov beat ("One for the widows, at least"),
but has no mechanical effect on the Selengrad plan. Optional.

## Parser verbs

- `EXAMINE PANEL` / `EXAMINE STENCIL` — see the classified markings
- `OPEN PANEL` — refused until `cannon-accessible`
- `ASK PETROV ABOUT PANEL` / `ASK PETROV ABOUT STATION` — reveal + code
- `ENTER CODE XXXX` or `UNLOCK PANEL WITH CODE` — (simpler: just OPEN
  PANEL after Petrov reveals the code and sets the state)
- `EXAMINE FIRE CONTROL` / `X CONSOLE` — see current threat list
- `AIM AT <target>` — set aim
- `FIRE CANNON` / `FIRE` — fire at last-aimed target

## Threat-list UX

After LISTEN at the fire-control console, populate:

```
Active tracks:
  1. ASAT-ALFA            range 380 km   closing         [HOSTILE]
  2. FREEDOM STATION      range 120 km   stable          [ALLIED]
  3. COSMOS-1402 (recon)  range 900 km   passive         [PASSIVE]
```

Display-only. No actual range simulation. Sets `target-known-asat`,
etc. truth states.

## State variables to add

```
cannon-revealed        (truth state; starts false)
cannon-accessible      (truth state; starts false)
targets-listed         (truth state; starts false)
asat-destroyed         (truth state; starts false)
chen-killed            (truth state; starts false)
cosmos-destroyed       (truth state; starts false)
asat-turns-remaining   (number that varies; initially 15; decreases
                        each turn once `targets-listed is true`)
```

Collision death: `asat-turns-remaining <= 0 and asat-destroyed is false`
ends the story.

## Story fit

The cannon reveal is the **second identity punch** of the prototype —
after the war reveal (Earth is dead) comes the Mir-3 reveal (your
home was a weapon). Lands between Restore Power and Transmit. Creates
a fresh Act 5.5 in the structure doc.

- Morally: the player is now in possession of the only known
  functioning weapon in orbit, with 8 survivors and one lunar base.
- The ASAT forces the player to *use* the cannon. That use crosses
  a line even before the Freedom choice.
- Some players will then never consider Freedom. Some will.

## Minimal first cut

Ship in this order:

1. The reveal path (panel + stencil + ASK PETROV + code)
2. The ASAT threat + fire-control console + AIM + FIRE + destroy
3. Collision death if ignored
4. COSMOS-1402 (optional score, easy add)
5. Freedom Station branch (most content — separate PR)

Stages 1–3 make the cannon real and necessary. 4 adds flavor. 5 is
the dark choice we'll do last.

## Open questions

- Where exactly is the panel? Command Module wall? Corridor? (I'd
  say Command Module, next to the toolkit, so power-is-restored
  naturally gates the reveal.)
- How much ammunition? One shot? Three? (I'd say three — lets the
  player miss once and recover.)
- Should AIM be per-target or does `FIRE AT X` shortcut it? (Keep
  AIM explicit — the station is the cannon; aiming feels heavier.)
- Should Yevgenia express an opinion? (Yes — she's the engineer who
  didn't know about the cannon. Anger then pragmatism.)
