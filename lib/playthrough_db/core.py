"""
Core SQLite-backed playthrough storage.

Schema is created on first connect. All writes are inside a single
transaction so a failure rolls back cleanly. Reads use simple SELECTs
returning dicts (sqlite3.Row → dict).
"""

from __future__ import annotations

import json
import os
import pathlib
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Iterator, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "playthroughs.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id           TEXT PRIMARY KEY,
    started_at   TEXT NOT NULL,
    ended_at     TEXT,
    status       TEXT NOT NULL,
    ending_type  TEXT,
    final_score  INTEGER,
    final_o2     INTEGER,
    final_morale INTEGER,
    player_kind  TEXT,
    game_version TEXT,
    notes        TEXT
);

CREATE TABLE IF NOT EXISTS turns (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_number  INTEGER NOT NULL,
    command      TEXT,
    response     TEXT,
    o2           INTEGER,
    morale       INTEGER,
    current_room TEXT,
    inventory    TEXT,
    truth_states TEXT
);

CREATE TABLE IF NOT EXISTS ai_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_id         INTEGER REFERENCES turns(id) ON DELETE SET NULL,
    role            TEXT NOT NULL,
    model           TEXT,
    prompt_hash     TEXT,
    response        TEXT,
    cost_usd        REAL,
    input_tokens   INTEGER,
    output_tokens  INTEGER
);

CREATE TABLE IF NOT EXISTS ship_state_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_id       INTEGER REFERENCES turns(id) ON DELETE SET NULL,
    snapshot_json TEXT
);

CREATE TABLE IF NOT EXISTS metadata (
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    key        TEXT NOT NULL,
    value      TEXT,
    PRIMARY KEY (session_id, key)
);

CREATE INDEX IF NOT EXISTS idx_turns_session       ON turns(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_calls_session    ON ai_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_ship_state_session  ON ship_state_snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_ended_at   ON sessions(ended_at);
"""

_lock = threading.Lock()


def _resolve_db_path(db_path: Optional[pathlib.Path]) -> pathlib.Path:
    if db_path is not None:
        return pathlib.Path(db_path).expanduser()
    env = os.environ.get("MIRSEND_DB_PATH")
    if env:
        return pathlib.Path(env).expanduser()
    return DEFAULT_DB_PATH


@contextmanager
def _connect(db_path: Optional[pathlib.Path] = None) -> Iterator[sqlite3.Connection]:
    path = _resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[pathlib.Path] = None) -> pathlib.Path:
    """Create the schema if absent. Idempotent. Returns the resolved path."""
    path = _resolve_db_path(db_path)
    with _lock, _connect(db_path) as conn:
        conn.executescript(_SCHEMA)
    return path


def write_session(
    session: dict[str, Any], db_path: Optional[pathlib.Path] = None
) -> dict[str, int]:
    """
    Write a complete session to the database. Idempotent on session_id:
    re-writing the same id replaces all child rows (turns, ai_calls,
    snapshots) and updates the session row.

    Expected shape:

    {
      "session_id": "<uuid>",
      "started_at": "ISO8601",
      "ended_at": "ISO8601" | None,
      "status": "completed" | "in_progress" | "abandoned",
      "ending_type": "transmit" | ... | None,
      "final_score": int | None,
      "final_o2": int | None,
      "final_morale": int | None,
      "player_kind": "human" | "agent:<model>" | "test:<spec>",
      "game_version": "v0.2.0-alpha" | None,
      "notes": str | None,
      "turns": [ {turn_number, command, response, o2, morale,
                  current_room, inventory, truth_states}, ... ],
      "ai_calls": [ {turn_number, role, model, prompt_hash,
                     response, cost_usd, input_tokens,
                     output_tokens}, ... ],
      "ship_state_log": [ {turn_number, snapshot_json}, ... ],
      "metadata": { key: value, ... }
    }

    Returns counts: {sessions: 1, turns: N, ai_calls: M, snapshots: K, metadata: J}.
    """
    sid = session.get("session_id")
    if not isinstance(sid, str) or not sid:
        raise ValueError("session.session_id is required and must be a non-empty string")

    init_db(db_path)
    counts = {"sessions": 0, "turns": 0, "ai_calls": 0, "snapshots": 0, "metadata": 0}

    with _lock, _connect(db_path) as conn:
        # Upsert the session row.
        conn.execute(
            """
            INSERT INTO sessions (id, started_at, ended_at, status, ending_type,
                                  final_score, final_o2, final_morale,
                                  player_kind, game_version, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                started_at   = excluded.started_at,
                ended_at     = excluded.ended_at,
                status       = excluded.status,
                ending_type  = excluded.ending_type,
                final_score  = excluded.final_score,
                final_o2     = excluded.final_o2,
                final_morale = excluded.final_morale,
                player_kind  = excluded.player_kind,
                game_version = excluded.game_version,
                notes        = excluded.notes
            """,
            (
                sid,
                session.get("started_at"),
                session.get("ended_at"),
                session.get("status", "in_progress"),
                session.get("ending_type"),
                session.get("final_score"),
                session.get("final_o2"),
                session.get("final_morale"),
                session.get("player_kind"),
                session.get("game_version"),
                session.get("notes"),
            ),
        )
        counts["sessions"] = 1

        # Replace child rows for idempotent re-writes.
        conn.execute("DELETE FROM turns WHERE session_id = ?", (sid,))
        conn.execute("DELETE FROM ai_calls WHERE session_id = ?", (sid,))
        conn.execute("DELETE FROM ship_state_snapshots WHERE session_id = ?", (sid,))
        conn.execute("DELETE FROM metadata WHERE session_id = ?", (sid,))

        # Map turn_number -> turn_id so ai_calls and snapshots can link.
        turn_id_by_number: dict[int, int] = {}

        for turn in session.get("turns") or []:
            cur = conn.execute(
                """
                INSERT INTO turns (session_id, turn_number, command, response,
                                   o2, morale, current_room, inventory,
                                   truth_states)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    turn["turn_number"],
                    turn.get("command"),
                    turn.get("response"),
                    turn.get("o2"),
                    turn.get("morale"),
                    turn.get("current_room"),
                    json.dumps(turn["inventory"]) if turn.get("inventory") is not None else None,
                    json.dumps(turn["truth_states"]) if turn.get("truth_states") is not None else None,
                ),
            )
            turn_id_by_number[turn["turn_number"]] = cur.lastrowid
            counts["turns"] += 1

        for call in session.get("ai_calls") or []:
            tn = call.get("turn_number")
            conn.execute(
                """
                INSERT INTO ai_calls (session_id, turn_id, role, model,
                                      prompt_hash, response, cost_usd,
                                      input_tokens, output_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    turn_id_by_number.get(tn),
                    call["role"],
                    call.get("model"),
                    call.get("prompt_hash"),
                    call.get("response"),
                    call.get("cost_usd"),
                    call.get("input_tokens"),
                    call.get("output_tokens"),
                ),
            )
            counts["ai_calls"] += 1

        for snap in session.get("ship_state_log") or []:
            tn = snap.get("turn_number")
            conn.execute(
                """
                INSERT INTO ship_state_snapshots (session_id, turn_id, snapshot_json)
                VALUES (?, ?, ?)
                """,
                (
                    sid,
                    turn_id_by_number.get(tn),
                    json.dumps(snap["snapshot_json"])
                    if isinstance(snap.get("snapshot_json"), dict)
                    else snap.get("snapshot_json"),
                ),
            )
            counts["snapshots"] += 1

        meta = session.get("metadata") or {}
        for k, v in meta.items():
            conn.execute(
                "INSERT INTO metadata (session_id, key, value) VALUES (?, ?, ?)",
                (sid, str(k), str(v) if v is not None else None),
            )
            counts["metadata"] += 1

    return counts


def get_session(
    session_id: str, db_path: Optional[pathlib.Path] = None
) -> Optional[dict[str, Any]]:
    """
    Read back a complete session, including turns, ai_calls, snapshots,
    and metadata. Returns None if no session has that id.
    """
    init_db(db_path)
    with _lock, _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if row is None:
            return None

        out = dict(row)
        out["turns"] = [
            _row_to_turn(r)
            for r in conn.execute(
                "SELECT * FROM turns WHERE session_id = ? ORDER BY turn_number",
                (session_id,),
            ).fetchall()
        ]
        out["ai_calls"] = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM ai_calls WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        ]
        out["ship_state_log"] = [
            _row_to_snapshot(r)
            for r in conn.execute(
                "SELECT * FROM ship_state_snapshots WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        ]
        meta_rows = conn.execute(
            "SELECT key, value FROM metadata WHERE session_id = ?", (session_id,)
        ).fetchall()
        out["metadata"] = {r["key"]: r["value"] for r in meta_rows}
        return out


def _row_to_turn(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    if d.get("inventory"):
        d["inventory"] = json.loads(d["inventory"])
    if d.get("truth_states"):
        d["truth_states"] = json.loads(d["truth_states"])
    return d


def _row_to_snapshot(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    if d.get("snapshot_json"):
        try:
            d["snapshot_json"] = json.loads(d["snapshot_json"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


def list_sessions(
    *,
    limit: int = 100,
    player_kind: Optional[str] = None,
    ending_type: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> list[dict[str, Any]]:
    """
    Return session rows in reverse-chronological order, optionally filtered.

    `since` is an ISO8601 string; sessions with started_at >= since are returned.
    """
    init_db(db_path)
    where: list[str] = []
    args: list[Any] = []
    if player_kind is not None:
        where.append("player_kind = ?")
        args.append(player_kind)
    if ending_type is not None:
        where.append("ending_type = ?")
        args.append(ending_type)
    if since is not None:
        where.append("started_at >= ?")
        args.append(since)
    sql = "SELECT * FROM sessions"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY started_at DESC LIMIT ?"
    args.append(int(limit))

    with _lock, _connect(db_path) as conn:
        rows = conn.execute(sql, args).fetchall()
    return [dict(r) for r in rows]


def delete_session(
    session_id: str, db_path: Optional[pathlib.Path] = None
) -> bool:
    """
    Delete a session and all its child rows. Returns True if a row was
    removed, False if no session had that id.
    """
    init_db(db_path)
    with _lock, _connect(db_path) as conn:
        cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cur.rowcount > 0
