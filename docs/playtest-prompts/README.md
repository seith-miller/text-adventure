# Blind-playtest prompts

Three personas for unbiased player-perspective playthroughs via the `mirs-end` MCP. Use them when you need fresh eyes on the game and the team already knows the canonical arc too well to surface where new players actually get stuck.

## Why three personas

Different player styles surface different bugs. Running them in parallel produces a wider net than any single persona:

- **`cautious-explorer.md`** — reads everything, examines every noun, tries natural-language commands. Surfaces prose gaps, missing examinable scenery, breadcrumb failures.
- **`aggressive-verb-tryer.md`** — impatient, tries every synonym, escalates to weird commands when refused. Surfaces parser synonym gaps and refusal-message confusion.
- **`speedrunner.md`** — skims prose, looks for next verb, ignores flavor. Surfaces buried critical info, HELP/parser drift, pacing problems.

## How to run

### Via the Agent tool (in-conversation, fast)

```
Spawn 3 Agent calls in parallel, one per persona prompt. Each persona drives the mirs-end MCP for 25-30 turns and returns a structured report.
```

Output: 3 structured reports in conversation, ~10-15 min total. Suitable for spot-checks during a milestone.

### Via agent-lab (out-of-band, comprehensive)

```
For wave-level playtest passes, dispatch each persona to a separate worker via agent-lab.
```

Out-of-band reports land as PR comments or new issues. Suitable for nightly / pre-release passes.

## Triaging the output

Cluster findings by milestone using the `Routing recommendation` table pattern from issue #216. Most findings will route to **m4** (parser / mechanism) or **m6** (prose), not the milestone the playtest was scoped against. That's expected — UI-only issues are rare on a player-perspective playthrough.

## Hard rule

The personas must NEVER read source code, story.ni, or design docs. They play through the MCP only. The whole value of this technique is that it produces the same view a real new player gets — anything that breaks that frame invalidates the run.
