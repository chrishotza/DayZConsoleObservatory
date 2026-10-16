# Incident investigation — temporal correlation without overclaiming

## What this tool can show

DayZ Console Observatory groups **imported dated** ADM records into review windows when adjacent events are at most `gap_seconds` apart (300 seconds by default). The SQLite query orders strictly by server-local timestamps. Events with missing dates are **excluded** and the report says so. A temporal group is not proof of combat, collusion or misconduct.

An optional player ID anchors the search: the program scans all events in the requested time range, groups them chronologically and returns only the groups that contain that ID, preserving other players and unknown events in those same windows. Do **not** mistake an event appearing in the same group for a confirmed interaction.

## CLI examples

```powershell
dayz-observe incidents 2026-10-15T12:00:00 2026-10-15T12:30:00 --out share-summary.json
dayz-observe incidents 2026-10-15T12:00:00 2026-10-15T12:30:00 --server OWN_SERVICE --db observatory.db --player-id PLAYER_ID --gap-seconds 120 --out private-investigation.json --private
```

Both commands create new files and refuse overwriting existing files. **Aggregate-only is the default**, omitting server and player identities, source paths, timestamps, coordinates and raw lines. The private export contains all these data, plus deterministic per-record SHA-256 fingerprints, and must never be attached to public issues.

The dashboard's new **Incident timeline** makes the same search using the loopback-only API; detailed timestamps remain on the administrator's own computer. Do not expose the local API over the network because existing endpoints include private game records.

## Validation and boundaries

- Timestamp input is `YYYY-MM-DDTHH:MM:SS`, with no timezone offset. Use the *server's local clock*. The program does not convert to UTC.
- Windows may be 0–48 hours long, inclusive; default maximum scanned rows 500 (maximum supported 2,000).
- `gap_seconds` must be between 0 and 3,600. This defines **time adjacency**, not geographic distance.
- The row limit applies **before** player filtering. If `truncated=true`, tighten the interval; later matching groups may not appear.
- Imported ADM coordinate samples are sparse and may be five minutes apart. No interpolation, cheating accusation, live admin overlay or automated punishment is justified.
- Per-record SHA-256 fingerprints are consistency checks of `(path, generation, byte_offset, raw)`, **not authentic server attestations**.
- The current data classification parser is incomplete, and timestamps may be absent or discontinuous. Please treat incident groups as a human-review worklist.

## Still blocked on external validation

No live Nitrado/Xbox server access has been supplied. This version is tested with synthetic ADM fixtures only. For privileged in-game admin actions, an officially supported Bohemia interface is still required.
