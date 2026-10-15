"""Share-safe, read-only community validation diagnostics.

Never print player names, player or service IDs, tokens, paths, file names,
raw log events, server timestamps, or HTTP error bodies.
"""
from __future__ import annotations

from pathlib import Path
from .store import get_quality_report

SCHEMA = "dayz-observatory-beta-v1"


def probe_nitrado(api, service_id: int) -> dict:
    """Check remote service and log listing only; never download logs."""
    directory, service = api.discover_log_directory(service_id)
    entries = api.list_logs(service_id, directory)
    adm = [e for e in entries if str(e.get("name", "")).lower().endswith(".adm")]
    rpt = [e for e in entries if str(e.get("name", "")).lower().endswith(".rpt")]
    return {
        "schema": SCHEMA,
        "check": "nitrado-metadata-readonly",
        "result": "ok",
        "xbox_service_detected": service.get("game") == "dayzxb",
        "adm_files_visible": len(adm),
        "rpt_files_visible": len(rpt),
        "adm_metadata_cache_eligible": sum(
            isinstance(e.get("size"), (int, str))
            and not isinstance(e.get("size"), bool)
            and isinstance(e.get("modified_at"), (int, float, str))
            and not isinstance(e.get("modified_at"), bool)
            for e in adm
        ),
        "download_tested": False,
        "player_data_accessed": False,
        "notes": "Only service metadata and file listings were read, not log contents.",
    }


def offline_beta_report(db_path: str | Path, server: str = "default") -> dict:
    """Summarize local observations; never export player or server identities."""
    q = get_quality_report(db_path, server)
    return {
        "schema": SCHEMA,
        "check": "offline-ingestion-summary",
        "result": "ok",
        "events": int(q["events"]),
        "known_players_count": int(q["known_players"]),
        "position_observations": int(q["position_observations"]),
        "unclassified_events": int(q["unclassified_events"]),
        "undated_events": int(q["undated_events"]),
        "source_files_count": int(q["imported_sources"]),
        "notes": "Aggregate records only: no live player positions or server identity.",
    }
