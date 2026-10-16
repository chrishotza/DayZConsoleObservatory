"""Local-only SQLite health checks, safe snapshots and explicit retention.

Maintenance operations never connect to Nitrado or modify the game server.
The retention command performs logical deletion, NOT secure disk erasure.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime
import os
from pathlib import Path
import sqlite3

SCHEMA = "dayz-observatory-maintenance-v1"


def _existing_database(database: str | Path) -> Path:
    path = Path(database).expanduser().absolute()
    if path.is_symlink() or not path.is_file():
        raise ValueError("Database does not exist or is a symlink")
    return path


def _open_existing(path: Path, *, writable: bool = False) -> sqlite3.Connection:
    mode = "rw" if writable else "ro"
    uri = path.as_uri() + "?mode=" + mode
    db = sqlite3.connect(uri, uri=True, timeout=30, isolation_level=None)
    db.row_factory = sqlite3.Row
    return db


def _health(connection: sqlite3.Connection) -> bool:
    row = connection.execute("PRAGMA quick_check(1)").fetchone()
    return row is not None and row[0] == "ok"


def database_health(database: str | Path) -> dict:
    """Check existing SQLite database without creating files or exposing IDs."""
    path = _existing_database(database)
    try:
        with closing(_open_existing(path)) as db:
            integrity_ok = _health(db)
            if not integrity_ok:
                return {"schema": SCHEMA, "integrity_ok": False, "result": "corrupt"}
            events = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            sources = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
            undated = db.execute("SELECT COUNT(*) FROM events WHERE occurred_at IS NULL").fetchone()[0]
            server_count = db.execute("SELECT COUNT(DISTINCT server) FROM events").fetchone()[0]
        return {"schema": SCHEMA, "integrity_ok": True, "result": "ok",
                "events": events, "sources": sources,
                "undated_events": undated, "servers_with_events": server_count,
                "sensitive_data_on_disk": True}
    except sqlite3.DatabaseError:
        raise ValueError("Database format or schema is invalid") from None


def backup_database(database: str | Path, destination: str | Path) -> dict:
    """Consistent SQLite online backup to a new owner-private file, no clobbering."""
    source = _existing_database(database)
    destination = Path(destination).expanduser().absolute()
    if destination == source:
        raise ValueError("Backup destination must differ from source")
    destination.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(destination, flags, 0o600)
    os.close(fd)
    try:
        with closing(_open_existing(source)) as origin:
            if not _health(origin):
                raise ValueError("Source database failed SQLite integrity check")
            with closing(sqlite3.connect(destination)) as backup:
                origin.backup(backup)
        with closing(_open_existing(destination)) as check:
            if not _health(check):
                raise ValueError("Backup failed SQLite integrity check")
            event_count = check.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        if os.name == "posix":
            os.chmod(destination, 0o600)
        return {"schema": SCHEMA, "result": "saved", "verified": True,
                "events": event_count, "contains_private_player_data": True,
                "warning": "This backup includes private player data; never upload it publicly."}
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def _cutoff(value: str) -> str:
    if not isinstance(value, str) or len(value) != 19 or value[4:5] != "-" or value[10:11] != "T":
        raise ValueError("Cutoff must be YYYY-MM-DDTHH:MM:SS in server-local time")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        raise ValueError("Invalid server-local cutoff") from None
    if parsed.strftime("%Y-%m-%dT%H:%M:%S") != value:
        raise ValueError("Cutoff must be a canonical server-local datetime")
    return value


def retain_recent(database: str | Path, server: str, before: str, *,
                  apply: bool = False, confirm_server: str | None = None) -> dict:
    """Count or logically delete a server's events before an explicit local cutoff.

    Unknown-dated events remain untouched. Source byte cursors are deliberately
    preserved to prevent unchanged files from recreating deleted observations.
    """
    path = _existing_database(database)
    stamp = _cutoff(before)
    if not isinstance(server, str) or not server.strip() or len(server) > 256:
        raise ValueError("Invalid server identifier")
    if apply and confirm_server != server:
        raise ValueError("Applying retention requires --confirm-server matching --server")
    try:
        with closing(_open_existing(path, writable=apply)) as db:
            if not _health(db):
                raise ValueError("Database failed integrity check")
            if apply:
                db.execute("BEGIN IMMEDIATE")
            try:
                eligible = db.execute("""SELECT COUNT(*) FROM events
                    WHERE server=? AND occurred_at IS NOT NULL AND occurred_at<?""",
                    (server, stamp)).fetchone()[0]
                preserved_unknown = db.execute("""SELECT COUNT(*) FROM events
                    WHERE server=? AND occurred_at IS NULL""", (server,)).fetchone()[0]
                if apply:
                    changed = db.execute("""DELETE FROM events
                        WHERE server=? AND occurred_at IS NOT NULL AND occurred_at<?""",
                        (server, stamp)).rowcount
                    db.execute("COMMIT")
                else:
                    changed = 0
            except BaseException:
                if apply:
                    db.execute("ROLLBACK")
                raise
    except sqlite3.DatabaseError:
        raise ValueError("Database format or schema is invalid") from None
    return {"schema": SCHEMA, "mode": "apply" if apply else "dry-run",
            "eligible_events": eligible, "deleted_events": changed,
            "undated_preserved": preserved_unknown,
            "source_cursors_preserved": True,
            "warning": ("Logical SQLite deletion only: WAL, free pages, original logs and backups "
                        "may retain data. Explicit timestamps use server-local time; "
                        "no remote server records were changed.")}
