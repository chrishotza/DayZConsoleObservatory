"""Evidence-based, read-only player incident history; no inferred live positions."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3

from .store import connect


def _validate_player_id(player_id: str) -> str:
    """Keep query bounded; identifiers are opaque, never interpreted as SQL."""
    if not isinstance(player_id, str) or not player_id.strip() or len(player_id) > 256 or any(ord(c) < 32 for c in player_id):
        raise ValueError("Invalid player identifier")
    return player_id


def player_history(db_path: str | Path, server: str, player_id: str, limit: int = 300) -> dict:
    """Return historical observations and inferred *log* sessions for one stable ID.

    Connections without a matching disconnection are not evidence of an online user;
    they represent a log session with no observed end. File import order is never
    used to infer temporal sequence when timestamps are available.
    """
    player_id = _validate_player_id(player_id)
    limit = max(1, min(int(limit), 2000))
    with connect(db_path) as db:
        events = [dict(r) for r in db.execute("""
            SELECT occurred_at,clock,kind,player_name,player_id,x,z,altitude,
                   raw,path,generation,byte_offset
              FROM events WHERE server=? AND player_id=?
             ORDER BY (occurred_at IS NOT NULL) DESC, occurred_at DESC, id DESC
             LIMIT ?
        """, (server, player_id, limit))]

        # All dated connection/disconnection events, not only the visible page.
        edges = list(db.execute("""
            SELECT occurred_at,kind FROM events
             WHERE server=? AND player_id=? AND occurred_at IS NOT NULL
               AND kind IN ('connected','disconnected')
             ORDER BY occurred_at ASC, id ASC
        """, (server, player_id)))

        sessions: list[dict] = []
        opened: str | None = None
        for edge in edges:
            stamp, kind = edge["occurred_at"], edge["kind"]
            if kind == "connected":
                if opened is not None:
                    sessions.append({"connected_at": opened, "disconnected_at": None,
                                     "duration_seconds": None, "status": "missing_disconnect"})
                opened = stamp
            elif opened is None:
                sessions.append({"connected_at": None, "disconnected_at": stamp,
                                 "duration_seconds": None, "status": "missing_connect"})
            else:
                seconds = int((datetime.fromisoformat(stamp) - datetime.fromisoformat(opened)).total_seconds())
                sessions.append({"connected_at": opened, "disconnected_at": stamp,
                                 "duration_seconds": seconds if seconds >= 0 else None,
                                 "status": "complete" if seconds >= 0 else "invalid_clock"})
                opened = None
        if opened is not None:
            sessions.append({"connected_at": opened, "disconnected_at": None,
                             "duration_seconds": None, "status": "no_disconnection_observed"})

        latest = next((dict(occurred_at=e["occurred_at"], clock=e["clock"],
                            x=e["x"], z=e["z"], altitude=e["altitude"])
                       for e in events if e["x"] is not None), None)
    return {
        "server": server,
        "player_id": player_id,
        "events": events,
        "sessions": sessions,
        "latest_observation": latest,
        "disclaimer": "Historical ADM evidence only. Open log sessions do not prove online status.",
    }
