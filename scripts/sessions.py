#!/usr/bin/env python3
"""CLI for querying the MIR'S END playthrough database.

Usage:
    scripts/sessions.py list [--limit N] [--player-kind KIND] [--ending TYPE] [--since DATE]
    scripts/sessions.py show <session-id>
    scripts/sessions.py turns <session-id> [--turn N] [--range A-B]
    scripts/sessions.py ai-calls <session-id> [--role ROLE]
    scripts/sessions.py costs [--since DATE] [--by DIMENSION]
    scripts/sessions.py compare <id1> <id2>
    scripts/sessions.py export <session-id>
    scripts/sessions.py delete <session-id> [--confirm]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running from repo root: add lib/ to path
_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "lib"))

from playthrough_db import connect, init_db  # noqa: E402
from playthrough_db import queries  # noqa: E402

DEFAULT_DB = os.environ.get(
    "MIRSEND_DB", str(_repo_root / "data" / "playthroughs.db")
)

# ── Formatting helpers ───────────────────────────────────────────────


def _truncate(text: str | None, length: int = 60) -> str:
    if text is None:
        return ""
    text = text.replace("\n", " ")
    if len(text) > length:
        return text[: length - 3] + "..."
    return text


def _print_table(rows: list[dict], columns: list[tuple[str, int]]) -> None:
    """Print a simple aligned table."""
    if not rows:
        print("(no results)")
        return
    header = "  ".join(name.ljust(width) for name, width in columns)
    print(header)
    print("-" * len(header))
    for row in rows:
        parts = []
        for name, width in columns:
            val = row.get(name, "")
            parts.append(_truncate(str(val if val is not None else ""), width).ljust(width))
        print("  ".join(parts))


def _print_json(data: object) -> None:
    print(json.dumps(data, indent=2, default=str))


# ── Subcommand handlers ─────────────────────────────────────────────


def cmd_list(conn, args):
    rows = queries.list_sessions(
        conn,
        limit=args.limit,
        player_kind=args.player_kind,
        ending=args.ending,
        since=args.since,
    )
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows, [
            ("id", 20),
            ("started", 20),
            ("ended", 20),
            ("player_kind", 8),
            ("ending", 15),
            ("score", 8),
            ("turn_count", 6),
        ])


def cmd_show(conn, args):
    session = queries.get_session(conn, args.session_id)
    if session is None:
        print(f"Error: session '{args.session_id}' not found.", file=sys.stderr)
        sys.exit(1)
    if args.json:
        _print_json(session)
    else:
        for key, val in session.items():
            if key == "source_json":
                continue
            print(f"{key:20s}: {val}")


def cmd_turns(conn, args):
    range_start = range_end = None
    if args.range:
        parts = args.range.split("-")
        if len(parts) != 2:
            print("Error: --range must be A-B (e.g. 1-10).", file=sys.stderr)
            sys.exit(1)
        range_start, range_end = int(parts[0]), int(parts[1])

    rows = queries.get_turns(
        conn,
        args.session_id,
        turn=args.turn,
        range_start=range_start,
        range_end=range_end,
    )
    if not rows and not args.json:
        # Check if session exists at all
        if queries.get_session(conn, args.session_id) is None:
            print(f"Error: session '{args.session_id}' not found.", file=sys.stderr)
            sys.exit(1)
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows, [
            ("turn_number", 6),
            ("command", 30),
            ("response", 50),
            ("state", 30),
        ])


def cmd_ai_calls(conn, args):
    rows = queries.get_ai_calls(conn, args.session_id, role=args.role)
    if not rows and not args.json:
        if queries.get_session(conn, args.session_id) is None:
            print(f"Error: session '{args.session_id}' not found.", file=sys.stderr)
            sys.exit(1)
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows, [
            ("turn_number", 6),
            ("role", 12),
            ("model", 20),
            ("cost", 10),
            ("response", 50),
        ])


def cmd_costs(conn, args):
    rows = queries.cost_report(conn, since=args.since, by=args.by)
    if args.json:
        _print_json(rows)
    else:
        _print_table(rows, [
            ("group_key", 20),
            ("call_count", 10),
            ("total_cost", 12),
        ])


def cmd_compare(conn, args):
    result = queries.compare_sessions(conn, args.session_id_1, args.session_id_2)
    if result is None:
        print("Error: one or both sessions not found.", file=sys.stderr)
        sys.exit(1)
    if args.json:
        _print_json(result)
    else:
        s1 = result["session_1"]
        s2 = result["session_2"]
        diffs = result["diffs"]
        print(f"{'':20s}  {'Session 1':>15s}  {'Session 2':>15s}  {'Diff':>10s}")
        print("-" * 65)
        print(f"{'ID':20s}  {s1['id']:>15s}  {s2['id']:>15s}")
        print(f"{'Turn count':20s}  {s1['turn_count']:>15d}  {s2['turn_count']:>15d}  {diffs['turn_count']:>+10d}")
        print(f"{'Ending':20s}  {str(s1['ending']):>15s}  {str(s2['ending']):>15s}")
        print(f"{'Total cost':20s}  {s1['total_cost']:>15.4f}  {s2['total_cost']:>15.4f}  {diffs['cost']:>+10.4f}")
        print(f"{'AI calls':20s}  {s1['ai_call_count']:>15d}  {s2['ai_call_count']:>15d}  {diffs['ai_call_count']:>+10d}")
        print()
        print("AI call distribution:")
        all_roles = sorted(
            set(list(result["ai_distribution"][s1["id"]].keys()) + list(result["ai_distribution"][s2["id"]].keys()))
        )
        for role in all_roles:
            c1 = result["ai_distribution"][s1["id"]].get(role, 0)
            c2 = result["ai_distribution"][s2["id"]].get(role, 0)
            print(f"  {role:18s}  {c1:>15d}  {c2:>15d}  {c1 - c2:>+10d}")


def cmd_export(conn, args):
    data = queries.export_session(conn, args.session_id)
    if data is None:
        print(f"Error: session '{args.session_id}' not found.", file=sys.stderr)
        sys.exit(1)
    _print_json(data)


def cmd_delete(conn, args):
    if not args.confirm:
        print("Error: pass --confirm to delete a session.", file=sys.stderr)
        sys.exit(1)
    deleted = queries.delete_session(conn, args.session_id)
    if not deleted:
        print(f"Error: session '{args.session_id}' not found.", file=sys.stderr)
        sys.exit(1)
    print(f"Deleted session '{args.session_id}' and its child rows.")


# ── Argument parser ──────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sessions.py",
        description="Query the MIR'S END playthrough database.",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB,
        help="Path to the SQLite database (default: $MIRSEND_DB or data/playthroughs.db)",
    )

    subs = parser.add_subparsers(dest="command")

    # list
    p_list = subs.add_parser("list", help="List sessions")
    p_list.add_argument("--limit", type=int, default=50)
    p_list.add_argument("--player-kind", choices=["human", "agent", "test"])
    p_list.add_argument("--ending", type=str)
    p_list.add_argument("--since", type=str, help="ISO date (e.g. 2025-01-01)")
    p_list.add_argument("--json", action="store_true")

    # show
    p_show = subs.add_parser("show", help="Show session detail")
    p_show.add_argument("session_id")
    p_show.add_argument("--json", action="store_true")

    # turns
    p_turns = subs.add_parser("turns", help="Show turns for a session")
    p_turns.add_argument("session_id")
    p_turns.add_argument("--turn", type=int, help="Single turn number")
    p_turns.add_argument("--range", type=str, help="Turn range A-B")
    p_turns.add_argument("--json", action="store_true")

    # ai-calls
    p_ai = subs.add_parser("ai-calls", help="Show AI calls for a session")
    p_ai.add_argument("session_id")
    p_ai.add_argument("--role", choices=["station-ai", "director", "narrator"])
    p_ai.add_argument("--json", action="store_true")

    # costs
    p_costs = subs.add_parser("costs", help="Cost report")
    p_costs.add_argument("--since", type=str)
    p_costs.add_argument("--by", choices=["player", "role", "day"], default="player")
    p_costs.add_argument("--json", action="store_true")

    # compare
    p_compare = subs.add_parser("compare", help="Compare two sessions")
    p_compare.add_argument("session_id_1")
    p_compare.add_argument("session_id_2")
    p_compare.add_argument("--json", action="store_true")

    # export
    p_export = subs.add_parser("export", help="Export session as JSON")
    p_export.add_argument("session_id")

    # delete
    p_delete = subs.add_parser("delete", help="Delete a session")
    p_delete.add_argument("session_id")
    p_delete.add_argument("--confirm", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    conn = connect(args.db)

    dispatch = {
        "list": cmd_list,
        "show": cmd_show,
        "turns": cmd_turns,
        "ai-calls": cmd_ai_calls,
        "costs": cmd_costs,
        "compare": cmd_compare,
        "export": cmd_export,
        "delete": cmd_delete,
    }

    dispatch[args.command](conn, args)
    conn.close()


if __name__ == "__main__":
    main()
