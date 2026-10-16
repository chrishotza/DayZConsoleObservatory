"""Bounded, chronological incident clustering of already imported ADM evidence.

Proximity in server-local time is a review aid, not evidence of coordination,
movement between samples, guilt or live game state.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
import re
from typing import Any

from .casebook import _fingerprint
from .investigate import _validate_player_id
from .store import connect

SCHEMA = "dayz-observatory-incidents-v1"
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\Z")
MAX_WINDOW_HOURS = 48
MAX_RECORDS = 2000


def _parse_server_stamp(value: str) -> datetime:
    if not isinstance(value, str) or not STAMP.fullmatch(value):
        raise ValueError("Use server-local timestamps as YYYY-MM-DDTHH:MM:SS (without timezone)")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        raise ValueError("Invalid server-local timestamp") from None


def search_incidents(
    db_path: str | Path,
    server: str,
    start: str,
    end: str,
    *,
    gap_seconds: int = 300,
    max_records: int = 500,
    player_id: str | None = None,
    private: bool = False,
) -> dict[str, Any]:
    """Group observed events by maximum gap; optionally select groups with one player.

    The event cap is applied before filtering groups by player; truncation means
    later relevant groups may be missing, and is always called out.
    """
    begin = _parse_server_stamp(start)
    finish = _parse_server_stamp(end)
    if begin > finish or finish - begin > timedelta(hours=MAX_WINDOW_HOURS):
        raise ValueError("Time window must be increasing and no longer than 48 hours")
    if isinstance(gap_seconds, bool) or not isinstance(gap_seconds, int) or not 0 <= gap_seconds <= 3600:
        raise ValueError("gap_seconds must be an integer between 0 and 3600")
    if isinstance(max_records, bool) or not isinstance(max_records, int) or not 1 <= max_records <= MAX_RECORDS:
        raise ValueError("max_records must be an integer between 1 and 2000")
    if not isinstance(server, str) or not server.strip() or len(server) > 256:
        raise ValueError("Invalid server identifier")
    if player_id is not None:
        player_id = _validate_player_id(player_id)

    with connect(db_path) as db:
        records = [dict(row) for row in db.execute("""
            SELECT occurred_at,clock,kind,player_name,player_id,x,z,altitude,
                   path,generation,byte_offset,raw
            FROM events
            WHERE server=? AND occurred_at>=? AND occurred_at<=?
            ORDER BY occurred_at ASC,id ASC LIMIT ?
        """, (server, start, end, max_records + 1))]
    truncated = len(records) > max_records
    rows = records[:max_records]

    buckets: list[list[dict]] = []
    previous: datetime | None = None
    for record in rows:
        current = datetime.fromisoformat(record["occurred_at"])
        if previous is None or (current - previous).total_seconds() > gap_seconds:
            buckets.append([])
        buckets[-1].append(record)
        previous = current

    selected = [
        group for group in buckets
        if player_id is None or any(row["player_id"] == player_id for row in group)
    ]
    groups: list[dict[str, Any]] = []
    for i, group in enumerate(selected, start=1):
        item: dict[str, Any] = {
            "index": i,
            "record_count": len(group),
            "kind_counts": dict(sorted(Counter(row["kind"] for row in group).items())),
            "known_players": len({row["player_id"] for row in group if row["player_id"]}),
            "position_observations": sum(row["x"] is not None and row["z"] is not None for row in group),
            "source_generations": len({(row["path"], row["generation"]) for row in group}),
        }
        if private:
            item["first_observed"] = group[0]["occurred_at"]
            item["last_observed"] = group[-1]["occurred_at"]
            item["records"] = [
                {**row, "record_fingerprint_sha256": _fingerprint(row)}
                for row in group
            ]
        groups.append(item)
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "disclosure": "private" if private else "aggregate-only",
        "scope": "imported, dated ADM events on one server; temporal grouping only",
        "group_count": len(groups),
        "selected_records": sum(g["record_count"] for g in groups),
        "scanned_records": len(rows),
        "truncated": truncated,
        "undated_events_excluded": True,
        "player_filter_applied": player_id is not None,
        "warnings": [
            "Temporal proximity alone does not establish interaction, causality or misconduct.",
            "Server-local timestamps may have unknown timezones or discontinuities.",
            "Undated events are excluded; unknown and unlinked events can make evidence incomplete.",
            "Limits are applied before player filtering; truncated searches may omit relevant groups.",
            "Historical positions are sparse snapshots, not movement trajectories or live locations.",
        ],
        "groups": groups,
    }
    if private:
        report["query"] = {"server": server, "start": start, "end": end,
                           "gap_seconds": gap_seconds, "player_id": player_id}
    return report
