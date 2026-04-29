"""
Markdown formatter for playthrough sessions.

Lives in the playthrough_db package so any caller (the pool runner's
``dump`` subcommand, the playtest driver's auto-dump, future tooling)
can produce identical-shape transcripts without coupling on the
playtest scripts directly.
"""

from __future__ import annotations

import json


def format_session_markdown(session: dict) -> str:
    """
    Render a session row + its turns as a human-readable markdown
    transcript. Intended for skim review when iterating on the prose.

    Accepts the shape returned by ``playthrough_db.get_session`` and
    the shape produced by the playtest driver's summary (which already
    matches it).
    """
    sid = session.get("id") or session.get("session_id") or "(no id)"
    meta = session.get("metadata") or {}
    if isinstance(meta, list):
        meta = {entry.get("key"): entry.get("value") for entry in meta if entry}

    cost = meta.get("estimated_cost_usd", "?")
    bailout = meta.get("bailout_reason", session.get("status", "?"))
    turns = session.get("turns") or []
    player_kind = session.get("player_kind") or "(unknown)"
    ending = session.get("ending_type") or "(none)"
    started = session.get("started_at") or "?"
    score = session.get("final_score")
    o2 = session.get("final_o2")
    morale = session.get("final_morale")

    lines: list[str] = []
    lines.append(f"# Playthrough {sid} - {player_kind}")
    lines.append("")
    lines.append(
        f"started: {started} · turns: {len(turns)} · "
        f"status: {session.get('status', '?')} · ending: {ending} · "
        f"cost: ${cost}"
    )
    lines.append(
        f"final score: {score} · O2: {o2} · morale: {morale} · bailout: {bailout}"
    )

    stuck_meta = meta.get("stuck_moments")
    if stuck_meta:
        try:
            stuck_entries = json.loads(stuck_meta)
        except (ValueError, TypeError):
            stuck_entries = []
        if stuck_entries:
            lines.append("")
            lines.append("**Stuck moments:**")
            for entry in stuck_entries:
                lines.append(
                    f"- turns {entry.get('turn_start')}-{entry.get('turn_end')} "
                    f"in {entry.get('room', 'unknown')}"
                )

    lines.append("")
    lines.append("---")
    lines.append("")

    for turn in turns:
        n = turn.get("turn_number", "?")
        cmd = (turn.get("command") or "").strip() or "(empty)"
        room = turn.get("current_room") or "?"
        resp = (turn.get("response") or "").strip() or "(no response)"
        lines.append(f"## Turn {n}: `{cmd}`")
        lines.append(f"_room: {room}_")
        lines.append("")
        lines.append(resp)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
