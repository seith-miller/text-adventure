"""
Playthrough database for MIR'S END.

Stores every playthrough (human, agent, test) in a single SQLite file
so longitudinal analysis is possible: ending distribution, voice-drift
detection, cost reporting, regression checks against the canonical arc.

## Public API

```python
from playthrough_db import (
    init_db,           # creates schema if absent
    write_session,     # idempotent on session_id
    get_session,
    list_sessions,
    delete_session,
)
```

## Storage

Default path: `data/playthroughs.sqlite` relative to the repo root.
Override via the `MIRSEND_DB_PATH` env var or by passing `db_path=` to
the public functions.

## Idempotency

`write_session(session_dict)` upserts on `session_id`. Re-POSTing the
same session updates the row in place; turns and AI calls are deleted
and re-inserted so an export-then-export does not duplicate.

## Why SQLite

Single-developer project. Local-first. No concurrent writers. Decades
of history fit comfortably in a few hundred MB. Any visualization tool
or query CLI can read the same file with no server. Move to Postgres
later if multiple players or a remote sync ever happens.
"""

from .core import (
    DEFAULT_DB_PATH,
    delete_session,
    get_session,
    init_db,
    list_sessions,
    write_session,
)
from .formatting import format_session_markdown
from .normalize import normalize_session_payload
from .queries import (
    commands_attempted,
    ending_distribution,
    fastest_path_to_ending,
    session_summaries,
    stuck_moments,
    stuck_moments_for_session,
    turns_to_first_argon_call,
    unrecognized_commands,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "commands_attempted",
    "delete_session",
    "ending_distribution",
    "fastest_path_to_ending",
    "format_session_markdown",
    "get_session",
    "init_db",
    "list_sessions",
    "normalize_session_payload",
    "session_summaries",
    "stuck_moments",
    "stuck_moments_for_session",
    "turns_to_first_argon_call",
    "unrecognized_commands",
    "write_session",
]
