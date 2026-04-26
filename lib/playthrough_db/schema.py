"""Database schema and connection helpers for the playthrough database."""

import sqlite3
from pathlib import Path

SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    started     TEXT NOT NULL,
    ended       TEXT,
    player_kind TEXT NOT NULL DEFAULT 'human',
    ending      TEXT,
    score       REAL,
    source_json TEXT
);

CREATE TABLE IF NOT EXISTS turns (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    command     TEXT,
    response    TEXT,
    state       TEXT
);

CREATE TABLE IF NOT EXISTS ai_calls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    role        TEXT NOT NULL,
    model       TEXT,
    cost        REAL DEFAULT 0,
    response    TEXT
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection with foreign-key enforcement enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Create tables (idempotent) and return the connection."""
    conn = connect(db_path)
    conn.executescript(SCHEMA_SQL)
    return conn
