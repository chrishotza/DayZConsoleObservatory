# Changelog

## Unreleased

- Close expected loopback HTTP error responses in browser/HTTP tests to prevent unraisable ResourceWarnings under strict Windows Python 3.14 test runs (HTTP 400/403/404/415).
- Close Nitrado HTTP error response bodies on retries, terminal API errors and signed-download failures, avoiding unraisable Python 3.14 `ResourceWarning` on simulated HTTP 429 and preserving existing file rollback/security behavior.
- Added offline regression coverage for response cleanup on HTTP 429/503/403 and failed signed downloads; independent Windows/macOS validation remains separate from CI.
- Browser import now reports a count of unfinished trailing-line bytes, without exposing log text. Pending lines remain uncommitted until reimported after completion.
- Hardened synthetic-tested ADM parser: reject invalid header dates/times and non-finite coordinates without fabricating observations.
- Avoid false death/combat/building matches from keywords embedded within other words, while preserving unknown timestamped records.
- Added parser and SQLite ingestion regression tests; real-world ADM coverage still requires consent-based validation.

## 0.8.0 — 2026-10-16

- Rebuilt browser workspace with a clear first-run flow, private local ADM upload and isolated synthetic demonstration.
- Added the Windows double-click launcher (`START_HERE.cmd`) and a dependency-free Python browser launcher.
- Added local upload CSRF/Origin/Host controls, strict filename/content-length bounds and browser HTTP regressions.
- Created a compact root README, structured machine-readable project index, AI-first navigation, and a single linked documentation index.
- UI provides historical records only. Live Xbox Nitrado service compatibility and in-game spectator controls remain unverified/unimplemented.



## 0.7.0 — 2026-10-15

- Added read-only SQLite health checks with aggregate-only diagnostics.
- Added consistent, integrity-verified online SQLite backup; exclusive file creation and restricted file permissions.
- Added per-server retention with dry-run default, explicit cutoff and exact server confirmation before applying.
- Preserved undated evidence and ingestion cursors, with honest warnings about WAL, SQLite freelist, original ADM files and backups.
- Added offline failure, privacy, backup and retention tests; no Nitrado credentials or DayZ required.
- All operations affect the local database only; Xbox/Nitrado production compatibility remains unverified.


## 0.6.0 — 2026-10-15

- Added bounded, server-local temporal incident grouping from dated ADM evidence.
- Added optional player-anchored context, chronological clusters, provenance-backed private exports and aggregate-only default sharing.
- Added local timeline UI and a loopback-only HTTP incident endpoint, strict time validation and regression tests.
- No live Nitrado validation, in-game observer/teleport capability, or publisher approval is implied.


## 0.5.1 — 2026-10-15

- Added aggregate-only case summaries and explicit private incident exports with per-record fingerprints.
- Enforced owner-only, exclusive new-file creation for evidence JSON; reports cannot overwrite existing paths.
- Hardened ADM ingester to detect same-inode, same-size rewrites and replaced consumed bytes.
- Added privacy regression tests and human-review evidence documentation.
- Still requires field validation against a consenting Xbox/Nitrado server owner.


## 0.5.0 — 2026-10-15

- Added foreground watch mode for bounded, read-only Nitrado sync; conservative 300-second default and hard 60-second minimum.
- Added aggregate-only JSON polling output, automatic stop after three consecutive unsuccessful cycles, and offline watch regression tests.
- Clarified product tracks: externally verifiable observability versus proposed, permissioned in-game capabilities.
- No live Nitrado integration validation or publisher authorization yet.


## 0.4.2 — 2026-10-15

- Added an entirely offline, end-to-end Nitrado API simulation: dayz-observe selftest.
- Fixed duplicated ADM events after atomic download of appended logs.
- Added SHA-256 digest verification of ingested bytes and backward-compatible SQLite migration.
- Added regression tests for log replacement, same-prefix rewrites and old database migrations.
- Opened community contribution roadmap, safer GitHub issue and pull-request templates, and CI selftest.
- No live Nitrado Xbox server has yet been verified. This remains a read-only experimental tool.

## 0.4.1

- Community beta and privacy-safe metadata probe.

## 0.4.0

- Multi-file sync, metadata-aware cache, dry-run, retry handling and security tests.