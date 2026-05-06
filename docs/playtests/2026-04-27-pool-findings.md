# Playtest pool findings - 2026-04-27

8 sessions, claude-sonnet-4-5, max-turns 100, total cost $5.10.
Source data: `data/playthroughs.sqlite` and `docs/playtests/runs/2026-04-27-*.md`.

## Headline

**0 of 8 sessions reached an ending.** Every run hit the 100-turn cap or
bailed out. The agent never engaged Argon-87. Not once.

We're not yet communicating clearly enough for a fresh player to find
the win conditions.

## The three blockers

### 1. The notebook can't be read

Yevgenia's notebook holds the burn calculation and (presumably) the
safe code. Every agent finds it, examines it, and is told:

> A water-stained field notebook. Half in Cyrillic shorthand. Half in
> numbers. Yevgenia's handwriting. The last entries fill most of a page
> and are dated tonight. You could read it.

But none of these work:

| verb | response |
|---|---|
| `read notebook` | (just re-reads the description) |
| `read it` | (same) |
| `read last entries` | "You can't see any such thing." |
| `consult notebook` | "I didn't understand that sentence." |
| `look up X in notebook` | "You discover nothing of interest." |
| `skim notebook` | "That's not a verb I recognise." |
| `search notebook` | "You find nothing of interest." |
| `open notebook` | "It isn't something you can open." |

The prose says "You could read it" but the parser rejects every read
verb. This is the single biggest blocker. Every Act-1 path goes through
this notebook.

### 2. Argon-87 is invisible

Zero of 8 sessions tried to talk to Argon, the station AI, or anything
addressable by `talk to`, `ask`, `argon`, `station ai`. The persona
exists (Part 9B in `story.ni` adds the grammar) but nothing in the
prose hints that there is anyone to talk to. The Main Corridor prose
mentions Yevgenia's body and Petrov's body, both already-dead crew,
but no AI presence.

The station feels derelict, which is the prose intent — but it leaves
the player no reason to issue an `ask argon about X` command.

### 3. Consoles are fixed in place

The Soyuz de-orbit console and the Command Module status console reject:

| verb | response |
|---|---|
| `activate console` | "That's not a verb I recognise." |
| `use console` | "I didn't understand that sentence." |
| `turn on console` | "It isn't something you can switch." |
| `push console` | "It is fixed in place." |

Players see "The de-orbit console is dark" and want to do something
about it. They don't know that power has to be restored elsewhere
first, and the console itself doesn't say so. This locks them out of
the Soyuz route.

## Parser gaps (vocabulary players reach for)

Across 8 sessions, top failed commands:

| Command | Count | Notes |
|---|---|---|
| `examine earth` | 7 | Cupola viewport shows Earth; players can't examine it |
| `take clipboard` | 7 | "A clipboard" is in the Main Corridor prose; not takeable |
| `examine control panels` | 6 | Plural — Command Module says "Every panel is dead" |
| `consult notebook` | 6 | See blocker #1 |
| `read last entries` | 5 | See blocker #1 |
| `use console` | 5 | See blocker #3 |
| `activate console` | 5 | Same |
| `use multimeter on panel` | 4 | Can't apply tools to objects |
| `examine cables` | 4 | Maintenance panel mentions cables |
| `initiate de-orbit` | 4 | Want to fly home but no verb |
| `examine bunks` | repeated | Bunks are in the Crew Quarters prose |
| `take pen` & `take borscht` | mixed | Pen takes; borscht has narrative refusal |

The pattern: **the prose mentions an object, the player tries to
interact with it, the parser says "you can't see any such thing".**
This breaks immersion immediately. Players learn the hard way that
prose objects ≠ interactable objects.

## Safe-code attempts (guessing)

Without the notebook readable, players guess at codes:

- `enter 1917 on safe`
- `enter 1945 on safe`
- `enter 1957 on safe`
- `type 1945 on keypad` → "That's not a verb I recognise."
- `set safe to 1917`
- `unlock safe` → "What do you want to unlock the classified safe with?"

They're picking Soviet historical dates. Whatever the real code is,
they're never going to land on it without being able to read the
notebook.

## Movement and exploration

Movement commands dominate (146 across 8 sessions). Agents do explore
the station thoroughly. They reach Crew Quarters → Main Corridor →
Life Support → Command Module → Soyuz Ferry → Hydroponics → Cupola →
Reactor → Progress Ferry. The map is legible. Compass + zenith/nadir
works. `go forward/aft` works alongside `north/south`.

What they can't do is **act** in those rooms once they arrive.

## Recommendations (in priority order)

1. **Make `read notebook` actually return content.** The single
   highest-leverage change. Have it print a multi-paragraph entry that
   includes:
   - the safe code (so players unlock КАТАЛОГ ВМФ-07)
   - the burn calculation (so the Soyuz route opens)
   - a hint at Argon ("ARGON-87 still online?", "ask the station AI
     about transmit")
2. **Add a clear "ask argon" cue** — somewhere visible early. Options:
   - Yevgenia's notebook says "Argon-87 still online — talk to him about [X]".
   - Argon initiates: a one-line ambient line in Main Corridor like
     *"A speaker clicks to life. 'I am still here.' The voice is
     synthesized but not unfamiliar."*
   - Add Argon's name to the Command Module description as "Argon's
     terminal, dark for now."
3. **`type CODE on keypad` and `enter CODE on safe`** should both work.
   These are the verbs every player reached for.
4. **`read X` should accept named subsections.** "read last entries",
   "read notes" — at minimum, `read X` should always return content
   for readable objects, not just the description.
5. **Make `examine bunks`, `examine clipboard`, `examine earth`,
   `examine control panels`, `examine cables` return something** —
   even if it's prose-only ("You see four bunks. Three are empty
   harnesses. The fourth was yours."). Anything is better than "You
   can't see any such thing."
6. **Console interactions need a verb.** Either `power on console` (and
   gate it on power restored) or `interact with console` should
   produce a meaningful response — even a refusal is better than
   "fixed in place."
7. **`take clipboard`, `take manual`, `take screwdriver from yevgenia`** —
   at least give them takable shadow versions. The prose advertises
   them; at minimum reject with character ("You leave the clipboard
   floating. No more entries to make.").

## What a good run would look like

Argon engagement on turn 5-10 (after flashlight). Notebook read by
turn 15 with the safe code. Safe opened by turn 25 with cataloged
contents. Either Selengrad burn computed by turn 50 (Soyuz route) or
transmission decision committed by turn 60. Ending by turn 80-100.

Right now, the median session gets to "I have a notebook I can't read
and a safe I can't open" by turn 30 and spends the next 70 turns
trying every verb in the dictionary on those two objects.

## Methodology

Run via `scripts/playtest-pool.py run --runs 8 --concurrency 4
--max-turns 100`. Each driver: an Anthropic Claude session whose tool
catalog contains exactly four MCP tools (`mirs_end_start_game`,
`mirs_end_send_command`, `mirs_end_get_state`,
`mirs_end_export_transcript`) and nothing else. System prompt is one
sentence: "Play a text-based adventure game using the available tools."
The agent has no path to the codebase, the writing samples, or the
design docs. What you read in the transcripts is what an LLM with zero
game knowledge produced.

Per-session transcripts in `docs/playtests/runs/`.
