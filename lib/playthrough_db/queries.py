"""Read-only query functions for the playthrough database."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def _rows_to_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    """Convert sqlite3.Row results to plain dicts."""
    return [dict(row) for row in cursor.fetchall()]


# ── list ─────────────────────────────────────────────────────────────

def list_sessions(
    conn: sqlite3.Connection,
    *,
    limit: int = 50,
    player_kind: str | None = None,
    ending: str | None = None,
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Return session summaries with optional filters."""
    clauses: list[str] = []
    params: list[Any] = []

    if player_kind is not None:
        clauses.append("s.player_kind = ?")
        params.append(player_kind)
    if ending is not None:
        clauses.append("s.ending = ?")
        params.append(ending)
    if since is not None:
        clauses.append("s.started >= ?")
        params.append(since)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    sql = f"""
        SELECT s.id, s.started, s.ended, s.player_kind, s.ending, s.score,
               COUNT(t.id) AS turn_count
        FROM sessions s
        LEFT JOIN turns t ON t.session_id = s.id
        {where}
        GROUP BY s.id
        ORDER BY s.started DESC
        LIMIT ?
    """
    params.append(limit)
    return _rows_to_dicts(conn.execute(sql, params))


# ── show ─────────────────────────────────────────────────────────────

def get_session(conn: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
    """Return full session metadata, turn count, AI call count, and total cost."""
    row = conn.execute(
        """
        SELECT s.*,
               (SELECT COUNT(*) FROM turns t WHERE t.session_id = s.id) AS turn_count,
               (SELECT COUNT(*) FROM ai_calls a WHERE a.session_id = s.id) AS ai_call_count,
               (SELECT COALESCE(SUM(a.cost), 0) FROM ai_calls a WHERE a.session_id = s.id) AS total_cost
        FROM sessions s
        WHERE s.id = ?
        """,
        (session_id,),
    ).fetchone()
    return dict(row) if row else None


# ── turns ────────────────────────────────────────────────────────────

def get_turns(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    turn: int | None = None,
    range_start: int | None = None,
    range_end: int | None = None,
) -> list[dict[str, Any]]:
    """Return turns for a session, optionally filtered by number or range."""
    clauses = ["session_id = ?"]
    params: list[Any] = [session_id]

    if turn is not None:
        clauses.append("turn_number = ?")
        params.append(turn)
    elif range_start is not None and range_end is not None:
        clauses.append("turn_number BETWEEN ? AND ?")
        params.extend([range_start, range_end])

    where = " AND ".join(clauses)
    return _rows_to_dicts(
        conn.execute(
            f"SELECT turn_number, command, response, state FROM turns WHERE {where} ORDER BY turn_number",
            params,
        )
    )


# ── ai-calls ────────────────────────────────────────────────────────

def get_ai_calls(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    role: str | None = None,
) -> list[dict[str, Any]]:
    """Return AI calls for a session, optionally filtered by role."""
    clauses = ["session_id = ?"]
    params: list[Any] = [session_id]

    if role is not None:
        clauses.append("role = ?")
        params.append(role)

    where = " AND ".join(clauses)
    return _rows_to_dicts(
        conn.execute(
            f"SELECT turn_number, role, model, cost, response FROM ai_calls WHERE {where} ORDER BY turn_number",
            params,
        )
    )


# ── costs ────────────────────────────────────────────────────────────

def cost_report(
    conn: sqlite3.Connection,
    *,
    since: str | None = None,
    by: str = "player",
) -> list[dict[str, Any]]:
    """Aggregate costs grouped by the chosen dimension."""
    valid_dimensions = {"player", "role", "day"}
    if by not in valid_dimensions:
        raise ValueError(f"--by must be one of {valid_dimensions}")

    join = ""
    group_col = ""
    params: list[Any] = []

    if by == "player":
        join = "JOIN sessions s ON s.id = a.session_id"
        group_col = "s.player_kind AS group_key"
    elif by == "role":
        group_col = "a.role AS group_key"
    elif by == "day":
        join = "JOIN sessions s ON s.id = a.session_id"
        group_col = "DATE(s.started) AS group_key"

    where = ""
    if since is not None:
        if by in ("player", "day"):
            where = "WHERE s.started >= ?"
        else:
            where = "WHERE a.session_id IN (SELECT id FROM sessions WHERE started >= ?)"
        params.append(since)

    sql = f"""
        SELECT {group_col},
               COUNT(*) AS call_count,
               COALESCE(SUM(a.cost), 0) AS total_cost
        FROM ai_calls a
        {join}
        {where}
        GROUP BY group_key
        ORDER BY total_cost DESC
    """
    return _rows_to_dicts(conn.execute(sql, params))


# ── compare ──────────────────────────────────────────────────────────

def compare_sessions(
    conn: sqlite3.Connection,
    id1: str,
    id2: str,
) -> dict[str, Any] | None:
    """Side-by-side comparison of two sessions."""
    s1 = get_session(conn, id1)
    s2 = get_session(conn, id2)
    if s1 is None or s2 is None:
        return None

    def _ai_dist(sid: str) -> dict[str, int]:
        rows = conn.execute(
            "SELECT role, COUNT(*) AS cnt FROM ai_calls WHERE session_id = ? GROUP BY role",
            (sid,),
        ).fetchall()
        return {r["role"]: r["cnt"] for r in rows}

    return {
        "session_1": {"id": id1, **{k: s1[k] for k in ("turn_count", "ending", "total_cost", "ai_call_count")}},
        "session_2": {"id": id2, **{k: s2[k] for k in ("turn_count", "ending", "total_cost", "ai_call_count")}},
        "diffs": {
            "turn_count": s1["turn_count"] - s2["turn_count"],
            "cost": round(s1["total_cost"] - s2["total_cost"], 6),
            "ai_call_count": s1["ai_call_count"] - s2["ai_call_count"],
        },
        "ai_distribution": {
            id1: _ai_dist(id1),
            id2: _ai_dist(id2),
        },
    }


# ── export ───────────────────────────────────────────────────────────

def export_session(conn: sqlite3.Connection, session_id: str) -> dict[str, Any] | None:
    """Re-emit the original mirsend JSON for the session (round-trip)."""
    row = conn.execute(
        "SELECT source_json FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if row is None:
        return None
    if row["source_json"]:
        return json.loads(row["source_json"])
    # Fallback: reconstruct from DB rows
    session = get_session(conn, session_id)
    turns = get_turns(conn, session_id)
    ai_calls = get_ai_calls(conn, session_id)
    return {
        "session": {k: session[k] for k in ("id", "started", "ended", "player_kind", "ending", "score")},
        "turns": turns,
        "ai_calls": ai_calls,
    }


# ── delete ───────────────────────────────────────────────────────────

def delete_session(conn: sqlite3.Connection, session_id: str) -> bool:
    """Remove a session and its child rows. Returns True if a row was deleted."""
    cursor = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    return cursor.rowcount > 0
