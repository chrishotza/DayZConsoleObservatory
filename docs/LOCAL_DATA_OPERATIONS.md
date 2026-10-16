# Local SQLite integrity, backup and retention

**DayZ Console Observatory v0.7 — all commands operate only on the owner's local computer.** They do not connect to Nitrado, affect player sessions, or invoke an in-game admin interface.

## 1. Inspect database integrity

```powershell
dayz-observe doctor --db observatory.db
```

The command checks an existing SQLite database with `PRAGMA quick_check` in read-only mode and prints only aggregate counts (no service IDs, player names, coordinates or file paths). Missing databases are not silently created.

## 2. Save a private snapshot

```powershell
dayz-observe backup --db observatory.db --out private-backup.sqlite
```

SQLite's online backup API makes a consistent snapshot of the database, including committed WAL changes, while preserving the original. Existing destination files and symlinks are never overwritten. On POSIX systems the backup has `0600` permissions, and the copy is checked for SQLite integrity.

**Important:** The backup contains player identifiers, positions, event text and potentially private server information. It is not an anonymous report. Keep it local and access controlled, and never upload it to public issues. No encryption is implemented by this command.

## 3. Preview old-event retention

```powershell
dayz-observe retain --db observatory.db --server YOUR_SERVER --before 2026-10-01T00:00:00
```

By default, this is **dry-run only**. It counts dated events that precede the selected *exclusive* cutoff. Datetimes are interpreted in the server's local clock, without assuming UTC; use the same timezone as imported ADM headers.

To make the change locally and deliberately:

```powershell
dayz-observe retain --db observatory.db --server YOUR_SERVER --before 2026-10-01T00:00:00 --apply --confirm-server YOUR_SERVER
```

The confirmation must match the requested server **exactly**. SQLite applies the deletion inside a transaction. Other servers are unaffected. Undated events remain; the import cursors are preserved so unchanged log files are not automatically reinserted on the next read.

## Limitations that matter

- This is **logical SQLite deletion**, not cryptographic or certified secure erasure. Deleted bytes may persist temporarily in WAL, free pages, disk snapshots, filesystem journals or backups.
- Original local ADM/RPT downloads are **not deleted**. Source file rewrites or a database restoration can cause records to be ingested again.
- A local backup preserves potentially sensitive historical evidence. Follow community retention policies and consider operating-system encryption.
- The commands do not automatically rotate, remove or verify remote Nitrado records; no credentials are required.
- No server-local timezone is inferred. Do not convert dates silently or prune records whose date is missing.
- Start with `doctor`, optionally take a protected `backup`, and verify the dry-run count before an explicit `--apply`.
