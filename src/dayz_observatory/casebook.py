"""Local evidence case export with safe aggregate sharing by default.

Not forensic authentication: fingerprints detect changes to an exported record,
but cannot prove what happened inside the DayZ server.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .investigate import _validate_player_id, player_history
from .store import connect

SCHEMA = "dayz-observatory-case-v1"


def _fingerprint(row: dict[str, Any]) -> str:
    """Repeatable digest of recorded evidence identity, not an authenticity seal."""
    fields = [row.get(key) for key in ("path", "generation", "byte_offset", "raw")]
    data = json.dumps(fields, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def build_case(db_path: str | Path, server: str, player_id: str, *,
               private: bool = False, limit: int = 500) -> dict[str, Any]:
    """Default to aggregate-only export. Private mode must be explicitly requested.

    Counts apply only to events linked to the target player's stable ID. A
    complete server incident could contain other entries that cannot be linked.
    """
    player_id = _validate_player_id(player_id)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 2000:
        raise ValueError("limit must be an integer between 1 and 2000")

    history = player_history(db_path, server, player_id, limit)
    events = history["events"]
    with connect(db_path) as db:
        row = db.execute("SELECT COUNT(*) AS n FROM events WHERE server=? AND player_id=?",
                         (server, player_id)).fetchone()
        total = int(row["n"])
    kinds = dict(sorted(Counter(e["kind"] for e in events).items()))
    session_types = dict(sorted(Counter(s["status"] for s in history["sessions"]).items()))
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "disclosure": "private" if private else "aggregate-only",
        "scope": "one player identifier, available imported logs only",
        "event_count": len(events),
        "matched_event_count": total,
        "truncated": total > len(events),
        "counts_by_kind": kinds,
        "position_observations": sum(e["x"] is not None and e["z"] is not None for e in events),
        "session_status_counts": session_types,
        "source_generations": len({(e["path"], e["generation"]) for e in events}),
        "warnings": [
            "Historical ADM records only; no live location, player status or misconduct is established.",
            "Events not linked to this identifier are excluded; parsing may be incomplete.",
            "Server timestamps may have an unknown timezone; sessions may lack boundaries.",
            "Anomaly labels are not accusations or grounds for automatic punishment.",
        ],
    }
    if private:
        result["subject"] = {"server": server, "player_id": player_id}
        result["events"] = [{**e, "record_fingerprint_sha256": _fingerprint(e)} for e in events]
        result["sessions"] = history["sessions"]
        result["fingerprint_scope"] = "SHA-256 of JSON(path,generation,byte_offset,raw), not a cryptographic attestation"
    return result


def save_case(destination: str | Path, report: dict[str, Any]) -> None:
    """Create a new, owner-readable file; refuse existing paths and symlinks."""
    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
