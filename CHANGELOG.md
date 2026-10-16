# Changelog

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