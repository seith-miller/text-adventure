# AI Setup Guide

How to configure LLM-driven play and AI integrations for MIR'S END.

## MCP Server: LLM-as-Player

The MCP server lets an external LLM (Claude or any MCP-capable client) play
MIR'S END turn by turn through tool calls.

### Prerequisites

- Python 3.12+
- Node.js 18+ (for the game build)
- Playwright with Chromium (`npx playwright install chromium`)
- The `mcp` Python package (`pip install mcp`)

### Quick Start

1. **Build the story** (if not already built):

   ```bash
   npm run build:story
   ```

2. **Start the server** (stdio transport):

   ```bash
   python3 scripts/mirs_end_mcp.py
   ```

3. **Claude Code auto-discovery**: The `.mcp.json` in the repo root registers
   the server so Claude Code picks it up automatically. No manual config needed.

### Available Tools

| Tool | Description |
|------|-------------|
| `mirs_end_start_game()` | Start a new game session. Returns session ID, opening text, and initial state. |
| `mirs_end_send_command(session_id, command)` | Send a command and get the response. One call = one game turn. |
| `mirs_end_get_state(session_id)` | Read current room, O2, morale, inventory, score, and turn count. |
| `mirs_end_export_transcript(session_id)` | Export full transcript, command history, and final state. |
| `mirs_end_restart(session_id)` | Restart the game within an existing session. |
| `mirs_end_list_sessions()` | List all active sessions with start times and turn counts. |

### Architecture

The server uses **Playwright headless Chromium** to drive the existing web
harness (`game/play.html` + Quixe + GlkOte). Each session runs in its own
browser context, giving identical behavior to the real browser game.

```
LLM Client  <--stdio-->  MCP Server  <--Playwright-->  Chromium
                          (Python)                      game/play.html
                                                        Quixe + GlkOte
                                                        story.ulx
```

Sessions live in memory on the server process. State persists across tool
calls within a single server lifetime.

### Backend Choice

**Playwright** was chosen for the MVP because:

- The web harness already exists and is well-tested
- Playwright is already a project dependency (used in e2e tests)
- Behavior is identical to the real game (same interpreter, same UI)

**RemGlk** (a JSON-speaking Glk implementation paired with glulxe) would be
lighter weight but requires a non-default glulxe build. Migration to RemGlk
is a separate followup if resource usage becomes a concern.

### Running Tests

```bash
python3 -m pytest tests/test_mcp_server.py -v
```

Tests use a mock backend and do not require a browser or game binary.

## Shared LLM Bridge

The `lib/mirs_end_bridge/` package provides shared infrastructure consumed by
both the MCP server and the in-game Station AI runtime:

- **Game state parsing** (`game_state.py`): Extracts `[MIRSEND ...]` tokens
- **Prompt composition** (`prompts.py`): Builds prompts for any role
- **Claude wrapper** (`claude.py`): API calls with retry and cost accounting
- **Voice kit** (`voice_kit.py`): Loads writing samples and persona files
- **Logging** (`logs.py`): JSONL transcript of all LLM calls

See `lib/mirs_end_bridge/__init__.py` for the quick-start API example.
