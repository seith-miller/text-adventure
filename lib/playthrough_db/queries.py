"""
Aggregation queries over the playthrough database.

These power the m12 pool report: surfacing where players get stuck,
which commands they reach for that the parser doesn't know, and how
endings distribute across runs.

All queries take an optional `db_path`. Filters (`player_kind`, `since`)
narrow the rows considered. None means "all".

The "unrecognized command" detector matches Inform 7's standard parser-
rejection responses. Extend `UNRECOGNIZED_PATTERNS` if the story adds
new ones.
"""

from __future__ import annotations

import json
import pathlib
import re
from collections import Counter
from typing import Optional

from .core import _connect, init_db

UNRECOGNIZED_PATTERNS: tuple[str, ...] = (
    "I beg your pardon",
    "That's not a verb I recognise",
    "That's not a verb I recognize",
    "You can't see any such thing",
    "You can't go that way",
    "I don't understand",
    "I didn't understand",
    "What do you want to",
    "I only understood you as far as",
    "Nothing happens",
)
_UNRECOGNIZED_RE = re.compile(
    "|".join(re.escape(p) for p in UNRECOGNIZED_PATTERNS), re.IGNORECASE
)


def _build_where(
    player_kind: Optional[str],
    since: Optional[str],
    extra: Optional[str] = None,
    alias: str = "s",
) -> tuple[str, list]:
    """Build a WHERE clause from optional filters. Returns ('' or 'WHERE ...', params)."""
    clauses: list[str] = []
    params: list = []
    if player_kind is not None:
        clauses.append(f"{alias}.player_kind = ?")
        params.append(player_kind)
    if since is not None:
        clauses.append(f"{alias}.started_at >= ?")
        params.append(since)
    if extra:
        clauses.append(extra)
    if not clauses:
        return "", params
    return " WHERE " + " AND ".join(clauses), params


def commands_attempted(
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> Counter:
    """Count how often each verbatim command was attempted."""
    init_db(db_path)
    where, params = _build_where(player_kind, since, extra="t.command IS NOT NULL")
    sql = (
        "SELECT t.command FROM turns t "
        "JOIN sessions s ON s.id = t.session_id"
        f"{where}"
    )
    counter: Counter = Counter()
    with _connect(db_path) as conn:
        for row in conn.execute(sql, params):
            cmd = (row["command"] or "").strip().lower()
            if cmd:
                counter[cmd] += 1
    return counter


def unrecognized_commands(
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> Counter:
    """Count commands whose response matched a parser-rejection pattern."""
    init_db(db_path)
    where, params = _build_where(player_kind, since)
    sql = (
        "SELECT t.command, t.response FROM turns t "
        "JOIN sessions s ON s.id = t.session_id"
        f"{where}"
    )
    counter: Counter = Counter()
    with _connect(db_path) as conn:
        for row in conn.execute(sql, params):
            cmd = (row["command"] or "").strip().lower()
            resp = row["response"] or ""
            if cmd and _UNRECOGNIZED_RE.search(resp):
                counter[cmd] += 1
    return counter


def ending_distribution(
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> Counter:
    """Count sessions by ending_type, falling back to status when ending_type is null."""
    init_db(db_path)
    where, params = _build_where(player_kind, since)
    sql = f"SELECT ending_type, status FROM sessions s{where}"
    counter: Counter = Counter()
    with _connect(db_path) as conn:
        for row in conn.execute(sql, params):
            key = row["ending_type"] or row["status"] or "unknown"
            counter[key] += 1
    return counter


def stuck_moments_for_session(
    session_id: str, db_path: Optional[pathlib.Path] = None
) -> list[dict]:
    """
    Return the stuck-moments metadata recorded by the driver, if any.
    Each entry: ``{turn_start, turn_end, room, window}``.
    """
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM metadata WHERE session_id = ? AND key = 'stuck_moments'",
            (session_id,),
        ).fetchone()
    if row is None or not row["value"]:
        return []
    try:
        return json.loads(row["value"])
    except (ValueError, TypeError):
        return []


def stuck_moments(
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> Counter:
    """
    Aggregate stuck rooms across matching sessions. Counter key: room
    name. Value: number of distinct sessions that got stuck in that room.
    """
    init_db(db_path)
    where, params = _build_where(player_kind, since)
    sql = (
        "SELECT s.id AS sid, m.value AS val "
        "FROM sessions s LEFT JOIN metadata m "
        "ON m.session_id = s.id AND m.key = 'stuck_moments'"
        f"{where}"
    )
    counter: Counter = Counter()
    with _connect(db_path) as conn:
        for row in conn.execute(sql, params):
            if not row["val"]:
                continue
            try:
                entries = json.loads(row["val"])
            except (ValueError, TypeError):
                continue
            rooms = {e.get("room", "unknown") for e in entries if isinstance(e, dict)}
            for room in rooms:
                counter[room] += 1
    return counter


def session_summaries(
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> dict:
    """
    Pool-level stats: total runs, by-status counts, total cost.

    Cost comes from ``metadata.estimated_cost_usd`` (string, written by
    the playtest driver).
    """
    init_db(db_path)
    where, params = _build_where(player_kind, since)
    out = {"total": 0, "by_status": Counter(), "total_cost_usd": 0.0}
    with _connect(db_path) as conn:
        rows = list(conn.execute(
            f"SELECT id, status FROM sessions s{where}", params
        ))
        for row in rows:
            out["total"] += 1
            out["by_status"][row["status"] or "unknown"] += 1
            cost_row = conn.execute(
                "SELECT value FROM metadata "
                "WHERE session_id = ? AND key = 'estimated_cost_usd'",
                (row["id"],),
            ).fetchone()
            if cost_row and cost_row["value"]:
                try:
                    out["total_cost_usd"] += float(cost_row["value"])
                except (ValueError, TypeError):
                    pass
    out["total_cost_usd"] = round(out["total_cost_usd"], 4)
    return out


def turns_to_first_argon_call(
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> list[int]:
    """
    For each session, return the turn number of the first command that
    referenced Argon (the station AI). Sessions that never called Argon
    are omitted.
    """
    init_db(db_path)
    where, params = _build_where(player_kind, since)
    sql = (
        "SELECT t.session_id, t.turn_number, t.command "
        "FROM turns t JOIN sessions s ON s.id = t.session_id"
        f"{where} "
        "ORDER BY t.session_id, t.turn_number"
    )
    seen: dict[str, int] = {}
    with _connect(db_path) as conn:
        for row in conn.execute(sql, params):
            sid = row["session_id"]
            if sid in seen:
                continue
            cmd = (row["command"] or "").lower()
            if "argon" in cmd or "station ai" in cmd or "talk to ship" in cmd:
                seen[sid] = row["turn_number"]
    return sorted(seen.values())


def fastest_path_to_ending(
    ending_type: str,
    player_kind: Optional[str] = None,
    since: Optional[str] = None,
    db_path: Optional[pathlib.Path] = None,
) -> Optional[dict]:
    """
    Return the session with the fewest turns that reached `ending_type`.

    Returns ``{session_id, turn_count, command_path}`` or None.
    """
    init_db(db_path)
    where, params = _build_where(
        player_kind, since, extra="s.ending_type = ?"
    )
    params = list(params) + [ending_type]
    # Note: extra is a literal SQL fragment; we appended ending_type to params.
    sql = (
        "SELECT s.id AS sid, "
        "(SELECT COUNT(*) FROM turns t WHERE t.session_id = s.id) AS turn_count "
        f"FROM sessions s{where} "
        "ORDER BY turn_count ASC LIMIT 1"
    )
    with _connect(db_path) as conn:
        row = conn.execute(sql, params).fetchone()
        if row is None:
            return None
        path = [
            r["command"]
            for r in conn.execute(
                "SELECT command FROM turns WHERE session_id = ? "
                "ORDER BY turn_number",
                (row["sid"],),
            )
            if r["command"]
        ]
    return {
        "session_id": row["sid"],
        "turn_count": row["turn_count"],
        "command_path": path,
    }
