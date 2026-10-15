"""Pure parser for documented DayZ ADM log variants. Coordinates: X, Z, altitude.

Positions are observations, never predictions. Unrecognized timestamped lines are kept.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re

HEADER = re.compile(r"AdminLog started on\s+(\d{4}-\d{2}-\d{2})\s+at\s+\d{2}:\d{2}:\d{2}", re.I)
CLOCK = re.compile(r"^\s*(?P<clock>\d{2}:\d{2}:\d{2})\s*\|\s*(?P<body>.*)$")
PLAYER = re.compile(r'Player\s+"(?P<name>[^"]+)"\s*\(id=(?P<id>[^\s)]+)', re.I)
POS = re.compile(r'(?<![a-z])pos\s*=\s*<\s*(?P<x>-?\d+(?:\.\d+)?),\s*(?P<z>-?\d+(?:\.\d+)?),\s*(?P<alt>-?\d+(?:\.\d+)?)\s*>', re.I)


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
    return date.fromisoformat(m.group(1)) if m else None


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
    if "has been disconnected" in bodylow or "is disconnected" in bodylow:
        kind = "disconnected"
    elif "is connected" in bodylow:
        kind = "connected"
    elif "killed by" in bodylow or "was killed" in bodylow or "died" in bodylow:
        kind = "death"
    elif "hit by" in bodylow or "hit(" in bodylow or "damage" in bodylow:
        kind = "hit"
    elif "placed" in bodylow or "built" in bodylow or "dismantled" in bodylow:
        kind = "build"
    elif pos:
        kind = "position"
    else:
        kind = "unknown"
    return Event(clock=m.group("clock"), kind=kind,
        player_name=pm.group("name") if pm else None,
        player_id=pm.group("id") if pm else None,
        x=float(pos.group("x")) if pos else None,
        z=float(pos.group("z")) if pos else None,
        altitude=float(pos.group("alt")) if pos else None,
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
