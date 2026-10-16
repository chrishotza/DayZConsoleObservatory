"""Pure parser for documented DayZ ADM log variants. Coordinates: X, Z, altitude.

Positions are observations, never predictions. Unrecognized timestamped lines are kept.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
import math

HEADER = re.compile(r"AdminLog started on\s+(?P<date>\d{4}-\d{2}-\d{2})\s+at\s+(?P<time>\d{2}:\d{2}:\d{2})", re.I)
CLOCK = re.compile(r"^\s*(?P<clock>\d{2}:\d{2}:\d{2})\s*\|\s*(?P<body>.*)$")
PLAYER = re.compile(r'Player\s+"(?P<name>[^"]+)"\s*\(id=(?P<id>[^\s)]+)', re.I)
POS = re.compile(r'(?<![a-z])pos\s*=\s*<\s*(?P<x>-?\d+(?:\.\d+)?),\s*(?P<z>-?\d+(?:\.\d+)?),\s*(?P<alt>-?\d+(?:\.\d+)?)\s*>', re.I)

# Keep the deliberately small, synthetic-tested event grammar conservative.
# Whole words avoid false positives such as "studied" being labeled "died".
DEATH = re.compile(r"\\b(?:killed by|was killed|died)\\b", re.I)
HIT = re.compile(r"\\b(?:hit by|damage)\\b|\\bhit\\s*\\(", re.I)
BUILD = re.compile(r"\\b(?:placed|built|dismantled)\\b", re.I)


@dataclass(frozen=True)
class Event:
    clock: str | None
    kind: str
    player_name: str | None
    player_id: str | None
    x: float | None
    z: float | None
    altitude: float | None
    raw: str


def parse_header(line: str) -> date | None:
    m = HEADER.search(line)
    if m is None:
        return None
    try:
        # Validate the *whole* header timestamp, not only its calendar day.
        parsed = datetime.strptime(m.group("date") + " " + m.group("time"),
                                   "%Y-%m-%d %H:%M:%S")
        return parsed.date()
    except ValueError:
        return None


def parse_line(line: str) -> Event | None:
    """Parse one complete ADM line. Headers/separators are ignored."""
    raw = line.rstrip("\r\n")
    m = CLOCK.match(raw)
    if not m:
        return None
    try:
        datetime.strptime(m.group("clock"), "%H:%M:%S")
    except ValueError:
        return None
    body = m.group("body")
    pm = PLAYER.search(body)
    pos = POS.search(body)
    bodylow = body.lower()
    coordinates = None
    if pos:
        # A syntactically valid but huge numeric token can become +/-inf.
        # Never persist non-finite coordinates to SQLite / browser JSON.
        values = tuple(float(pos.group(key)) for key in ("x", "z", "alt"))
        if all(math.isfinite(value) for value in values):
            coordinates = values
    if "has been disconnected" in bodylow or "is disconnected" in bodylow:
        kind = "disconnected"
    elif "is connected" in bodylow:
        kind = "connected"
    elif DEATH.search(body):
        kind = "death"
    elif HIT.search(body):
        kind = "hit"
    elif BUILD.search(body):
        kind = "build"
    elif coordinates is not None:
        kind = "position"
    else:
        kind = "unknown"
    return Event(clock=m.group("clock"), kind=kind,
        player_name=pm.group("name") if pm else None,
        player_id=pm.group("id") if pm else None,
        x=coordinates[0] if coordinates is not None else None,
        z=coordinates[1] if coordinates is not None else None,
        altitude=coordinates[2] if coordinates is not None else None,
        raw=raw)


def event_datetime(clock: str | None, base_date: date | None, last_second: int | None, rollover: int) -> tuple[str | None, int | None, int]:
    if clock is None:
        return None, last_second, rollover
    h, m, s = map(int, clock.split(":"))
    seconds = h * 3600 + m * 60 + s
    if last_second is not None and last_second - seconds > 12 * 3600:
        rollover += 1
    moment = (base_date + timedelta(days=rollover)).isoformat() + "T" + clock if base_date else None
    return moment, seconds, rollover
