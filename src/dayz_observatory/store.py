"""Atomic, append-aware ADM ingestion and SQLite data access."""
from __future__ import annotations
from pathlib import Path
import sqlite3
from .parser import parse_header, parse_line, event_datetime
from datetime import date

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS sources (
 server TEXT NOT NULL, path TEXT NOT NULL,
 generation INTEGER NOT NULL DEFAULT 0,
 offset INTEGER NOT NULL DEFAULT 0,
 device INTEGER NOT NULL DEFAULT 0,
 inode INTEGER NOT NULL DEFAULT 0,
 prefix BLOB NOT NULL DEFAULT X'',
 base_date TEXT,
 last_second INTEGER,
 rollover INTEGER NOT NULL DEFAULT 0,
 PRIMARY KEY (server,path)
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 server TEXT NOT NULL, path TEXT NOT NULL,
 generation INTEGER NOT NULL, byte_offset INTEGER NOT NULL,
 occurred_at TEXT, clock TEXT, kind TEXT NOT NULL,
 player_name TEXT, player_id TEXT,
 x REAL, z REAL, altitude REAL, raw TEXT NOT NULL,
 UNIQUE(server,path,generation,byte_offset)
);
CREATE INDEX IF NOT EXISTS idx_events_server_time ON events(server,occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_player_time ON events(server,player_id,occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(server,kind);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(db_path), timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript(DDL)
    return db


def ingest(db_path: str | Path, source: str | Path, server: str="default") -> dict:
    """Only commit newline-terminated records. Never fabricate a date without a log header.

    Tracks per-source byte offsets and generations for rotation/truncation.
    """
    file = Path(source).expanduser().resolve()
    with file.open("rb") as fh:
        stat = file.stat()
        current_prefix = fh.read(128)
        with connect(db_path) as db:
            row = db.execute("SELECT * FROM sources WHERE server=? AND path=?", (server, str(file))).fetchone()
            generation = int(row["generation"]) if row else 0
            offset = int(row["offset"]) if row else 0
            last_second = row["last_second"] if row else None
            rollover = int(row["rollover"]) if row else 0
            base_date = date.fromisoformat(row["base_date"]) if row and row["base_date"] else None
            # Compare the prefix to the original prefix length (growth isn't a rewrite).
            prev_prefix = bytes(row["prefix"]) if row else b""
            rotated = bool(row and (
                (stat.st_ino != row["inode"] and row["inode"] != 0) or
                (stat.st_dev != row["device"] and row["device"] != 0) or
                stat.st_size < offset or
                current_prefix[:len(prev_prefix)] != prev_prefix
            ))
            if rotated:
                generation += 1
                offset, base_date, last_second, rollover = 0, None, None, 0
            fh.seek(offset)
            parsed, stored = 0, 0
            while True:
                position = fh.tell()
                chunk = fh.readline()
                if not chunk:
                    break
                if not chunk.endswith(b"\n"):
                    fh.seek(position)  # Wait until the writer finishes the record.
                    break
                raw = chunk.decode("utf-8-sig", errors="replace").rstrip("\r\n")
                new_base = parse_header(raw)
                if new_base:
                    base_date, last_second, rollover = new_base, None, 0
                event = parse_line(raw)
                if event is None:
                    continue
                parsed += 1
                timestamp, last_second, rollover = event_datetime(event.clock, base_date, last_second, rollover)
                cursor = db.execute("""INSERT OR IGNORE INTO events (
                    server,path,generation,byte_offset,occurred_at,clock,kind,
                    player_name,player_id,x,z,altitude,raw)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (server,str(file),generation,position,timestamp,event.clock,event.kind,
                     event.player_name,event.player_id,event.x,event.z,event.altitude,event.raw))
                stored += int(cursor.rowcount > 0)
            next_offset = fh.tell()
            # Freeze the prefix at first read; a short file can grow without changing its prefix.
            prefix = current_prefix if rotated or not row else prev_prefix
            db.execute("""INSERT INTO sources(server,path,generation,offset,device,inode,prefix,base_date,last_second,rollover)
                VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(server,path) DO UPDATE SET
                generation=excluded.generation,offset=excluded.offset,device=excluded.device,
                inode=excluded.inode,prefix=excluded.prefix,base_date=excluded.base_date,
                last_second=excluded.last_second,rollover=excluded.rollover""",
                (server,str(file),generation,next_offset,stat.st_dev,stat.st_ino,prefix,
                 base_date.isoformat() if base_date else None,last_second,rollover))
            return {"source":str(file),"server":server,"read_events":parsed,"new_events":stored,
                    "offset":next_offset,"generation":generation,"rotated":rotated}


def get_events(db_path: str | Path, server: str="default", kind: str | None=None, limit: int=300) -> list[dict]:
    limit = max(1,min(int(limit),2000))
    with connect(db_path) as db:
        query = "SELECT occurred_at,clock,kind,player_name,player_id,x,z,altitude FROM events WHERE server=?"
        args: list = [server]
        if kind:
            query += " AND kind=?"
            args.append(kind)
        query += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        return [dict(row) for row in db.execute(query,args)]


def get_players(db_path: str | Path, server: str="default") -> list[dict]:
    with connect(db_path) as db:
        # Last by event date rather than file import sequence. Unknown dates rank behind dated samples.
        query = """WITH ranked AS (
          SELECT player_id,player_name,occurred_at,clock,x,z,altitude,
            ROW_NUMBER() OVER (PARTITION BY player_id
              ORDER BY (occurred_at IS NOT NULL) DESC, occurred_at DESC, id DESC) AS rank
          FROM events WHERE server=? AND player_id IS NOT NULL AND x IS NOT NULL
        ) SELECT player_id,player_name,occurred_at,clock,x,z,altitude
          FROM ranked WHERE rank=1
          ORDER BY (occurred_at IS NOT NULL) DESC, occurred_at DESC LIMIT 250"""
        return [dict(row) for row in db.execute(query,(server,))]


def get_known_players(db_path: str | Path, server: str = "default") -> list[dict]:
    """Return stable player IDs from all logged events, even without positions."""
    with connect(db_path) as db:
        rows = db.execute("""WITH recent AS (
             SELECT player_id,player_name,occurred_at,
                    ROW_NUMBER() OVER (PARTITION BY player_id
                       ORDER BY (occurred_at IS NOT NULL) DESC,occurred_at DESC,id DESC) AS rn
             FROM events WHERE server=? AND player_id IS NOT NULL
           ) SELECT player_id,player_name,occurred_at FROM recent
             WHERE rn=1 ORDER BY player_name COLLATE NOCASE,player_id LIMIT 1500""", (server,))
        return [dict(r) for r in rows]
