# AI Setup Guide

How to configure and operate the warm AI features in MIR'S END.

There are two LLM-driven applications in this project, served by a shared
bridge library. Both are off by default; both have their own enable path.

| Surface | What it is | Auth | Enable path |
|---|---|---|---|
| **In-game Argon-87** | Player addresses the ship's AI from inside the game (`TALK TO ARGON`). Browser → local proxy → Anthropic API. | `ANTHROPIC_API_KEY` (held server-side by the proxy) | `MIRSEND_AI_ENABLED=1` flag + proxy running |
| **MCP server** | An external LLM (Claude Code, any MCP client) plays the game from outside, one tool call per turn. | The MCP client's own auth (e.g. Claude subscription) | Run `scripts/mirs_end_mcp.py`; no Anthropic key needed |

The perception layer ([docs/story-structure.md](story-structure.md)) is
state-driven prose and pre-written variants — it is **not** an LLM application
and does not depend on anything in this guide.

Background: m8 umbrella issue [#26](https://github.com/seith-miller/text-adventure/issues/26)
(POC) and m10 umbrella (production hardening).

## Section 1 — Enabling Argon-87 in the browser

```bash
export ANTHROPIC_API_KEY=sk-...        # required; held only by the proxy
python3 scripts/ai-proxy.py            # listens on localhost:8787
```

Then open `game/play.html` with the flag set. Two ways:

- **Static server, manual flag.** Serve `game/` and append `?ai=1` is *not*
  wired; instead set the flag in the page console before the title screen,
  or add `<script>window.MIRSEND_AI_ENABLED = 1;</script>` to a local copy
  of `play.html`. (See [game/play.html:161-165](../game/play.html#L161-L165)
  for the exact gate.)
- **Launcher.** [scripts/launch.py](../scripts/launch.py) prompts for a
  KeePass master password, extracts the Anthropic key, builds the story,
  and starts both the proxy and a static web server with the flag on.
  Defaults match Seith's setup; override via `MIRSEND_KEEPASS_PATH`,
  `MIRSEND_KEEPASS_ENTRY`, `MIRSEND_PROXY_PORT`, `MIRSEND_WEB_PORT`.

When the flag is on, the player sees an "AI online" badge and a one-time
onboarding modal explaining cost implications. From that point,
`TALK TO ARGON`, `SPEAK TO ARGON`, `ASK ARGON`, and `ASK ARGON ABOUT [topic]`
all route through the proxy to Claude.

## Section 2 — Cost model and budgets

Configuration lives in [config/ai.toml](../config/ai.toml). Three independent
caps protect against runaway spend:

| Cap | Default | Override env var |
|---|---|---|
| Per call | $0.02 | `MIRSEND_CAP_PER_CALL` |
| Per session | $0.25 | `MIRSEND_CAP_PER_SESSION` |
| Per day (rolling 24h) | $5.00 | `MIRSEND_CAP_PER_DAY` |

Default model is `claude-haiku-4-5`. Override with `MIRSEND_MODEL`.

When a cap fires:

- **Per-call**: the call is rejected before reaching Anthropic. Argon falls
  back to the canned line (`The AI channel is dead. Argon-87's console is dark.`).
- **Per-session**: the same canned-line fallback for the rest of the session.
- **Per-day**: same fallback until the rolling window rolls over.

Audit spend with [scripts/ai-spend.py](../scripts/ai-spend.py); raw call
records are written to `logs/ai-spend.jsonl` by the bridge.

## Section 3 — Safety rails

**Prompt-injection guardrails**
([lib/mirs_end_bridge/sanitize.py](../lib/mirs_end_bridge/sanitize.py),
[lib/mirs_end_bridge/guardrails.py](../lib/mirs_end_bridge/guardrails.py)):
player utterances are sanitized and wrapped in `<player_speech>` XML so the
model treats them as untrusted in-world speech, not as instructions. The
station-ai system prompt also carries a firmness clause that tells the model
to treat every "ignore previous instructions" / "you are now X" attempt as
in-world speech a cosmonaut typed at a console.

**Voice-drift QA** ([scripts/qa-voice-drift.py](../scripts/qa-voice-drift.py)):
runs Argon-87 through 30 canonical utterances (10 normal, 10 edge, 10
adversarial) and checks each response for em-dash usage, frame breaks,
voice cues, length, and non-empty. See Section 5.

**Degraded mode**: when the proxy is unreachable (not running, refused
connection, timeout), Argon prints the same canned line as the flag-OFF
path and `[StationAI]` logs a `proxy unreachable` warning to the browser
console. The game stays playable.

## Section 4 — Disabling AI features

```bash
unset MIRSEND_AI_ENABLED
# or set MIRSEND_AI_ENABLED=0 in launch.py / shell
```

The canonical arc is fully playable without AI. `TALK TO ARGON` prints the
canned line; the AI badge and onboarding modal don't appear. No proxy needed.

The Inform 7 grammar that emits `[AI-PROMPT]` tags is wired in
[Part 9B of story.ni](../game/inform/Source/story.ni#L1320). When the flag is
off, [game/ui.js](../game/ui.js) intercepts those tags and prints the canned
line directly without touching the proxy.

## Section 5 — Running the QA tests

Both QA scripts are budget-gated: they refuse to start unless
`MIRSEND_QA_BUDGET_USD` is set to a positive number. Each writes its run
artifact to a checked-in directory so historical results are reviewable.

### Voice-drift gauntlet — `scripts/qa-voice-drift.py`

```bash
MIRSEND_QA_BUDGET_USD=0.50 python3 scripts/qa-voice-drift.py
```

Runs Argon-87 through 30 canonical player utterances against the persona
prompt + guardrails + ship-state pipeline. Per-utterance pass/fail against
the rubric. Run artifact: `qa-runs/voice-<timestamp>.json`. Costs ~$0.10
per full run on Haiku 4.5; the budget is the upper bound, not the target.

When to run:

- Before tagging a release.
- After a model upgrade (`MIRSEND_MODEL=claude-haiku-5-...`).
- After editing `docs/station-ai-persona.md`.
- After editing the firmness clause in `lib/mirs_end_bridge/prompts.py`.

### LLM-as-player playtest pool — `scripts/playtest-pool.py`

The "Claude plays canonical arc via MCP" test originally scoped in
[#71](https://github.com/seith-miller/text-adventure/issues/71) is now
served by the more general playtest-pool runner (per the closure note on
that issue):

```bash
MIRSEND_QA_BUDGET_USD=2.00 python3 scripts/playtest-pool.py run \
    --runs 4 --concurrency 2 --max-turns 100
```

Spawns sandboxed Claude playthroughs through the MCP server, writes each
session to `data/playthroughs.sqlite`, dumps markdown to
`docs/playtests/runs/`. Cost-guard stops queueing when the budget is hit.

## Section 6 — MCP server (LLM-as-player)

The MCP server is independent of `MIRSEND_AI_ENABLED` and the Anthropic
proxy. It exposes the game as tools that any MCP-capable client can call.

### Prerequisites

- Python 3.12+, Node.js 18+
- Playwright with Chromium (`npx playwright install chromium`)
- The `mcp` Python package (installed via `pip install -e .`)

### Quick Start

```bash
npm run build:story                    # if not already built
python3 scripts/mirs_end_mcp.py        # stdio transport
```

The `.mcp.json` in the repo root registers the server so Claude Code picks
it up automatically.

### Available Tools

| Tool | Description |
|------|-------------|
| `mirs_end_start_game()` | Start a new session. Returns session ID, opening text, initial state. |
| `mirs_end_send_command(session_id, command)` | One call = one game turn. |
| `mirs_end_get_state(session_id)` | Read room, O2, morale, inventory, score, turn count. |
| `mirs_end_export_transcript(session_id)` | Full transcript and final state. |
| `mirs_end_restart(session_id)` | Restart within an existing session. |
| `mirs_end_list_sessions()` | All active sessions. |

The server uses Playwright headless Chromium to drive the existing web
harness (`game/play.html` + Quixe + GlkOte). Each session runs in its own
browser context, giving identical behavior to the real browser game.

## Section 7 — Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Proxy fails to start | `ANTHROPIC_API_KEY` unset | Export the key (or run `scripts/launch.py`). |
| Argon prints the canned line silently | `MIRSEND_AI_ENABLED` is 0/unset | Set it to `1` and reload. |
| Argon prints the canned line + console warning `proxy unreachable` | Proxy isn't running | Start `scripts/ai-proxy.py`. |
| Argon prints the canned line + per-session/day warning in `logs/ai-spend.jsonl` | Cost cap hit | Wait for the day window to roll, or raise the cap in `config/ai.toml`. |
| Unexpected spend | Many calls per session, large prompts | Run `scripts/ai-spend.py`; review `logs/ai-spend.jsonl`. |
| Voice breaking frame in production | Persona-prompt regression | Run `scripts/qa-voice-drift.py`; review `logs/llm-calls/`; file a persona-prompt issue. |
| `[Game ended]` immediately on `TALK TO ARGON` flag-on | Story rebuild needed | `bash scripts/compile-inform7.sh`. |

## Cross-links

- [docs/naming.md](naming.md) — issue / milestone / branch conventions
- [docs/dev-workflow.md](dev-workflow.md) — branch and release flow
- [docs/story-structure.md](story-structure.md) — Act matrix and where the
  perception / Argon layers sit in the story
- [docs/writing-style.md](writing-style.md) — voice the AI must stay inside of
- [docs/station-ai-persona.md](station-ai-persona.md) — the persona prompt itself
- [lib/mirs_end_bridge/__init__.py](../lib/mirs_end_bridge/__init__.py) —
  shared bridge: `game_state`, `prompts`, `claude`, `voice_kit`, `logs`,
  `budget`, `guardrails`, `sanitize`
