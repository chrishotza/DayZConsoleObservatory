# AI engineering handoff: DayZ Console Observatory

Project goal: legitimate, read-only administrative observability for DayZ Microsoft Store/Xbox (Nitrado). Source is open under MIT. Never imply official affiliation.

## Verified locally
- Python package entrypoint: `dayz-observe` (`src/dayz_observatory/cli.py`).
- ADM parser: `src/dayz_observatory/parser.py`. `pos=<X,Z,altitude>`; accepts optional `-`; preserves unknown timestamped lines.
- SQLite ingest: `src/dayz_observatory/store.py`. Byte offsets, pending line retry, rotation generation, rollover, chronological last-known position.
- `src/dayz_observatory/server.py`: loopback-only read API and static dashboard. No authentication; do NOT expose publicly.
- `src/dayz_observatory/nitrado.py`: read-only Microsoft/Xbox Nitrado API adapter. **Untested live; needs authorized service integration tests.**
- Tests: `PYTHONPATH=src python -m unittest discover -s tests -v` (24 passing as of 2026-10-15).

## Priorities (order)
1. Audit all API assumptions against documented Nitrado Xbox gameserver permissions; use private sample HTTP payloads with tokens removed.
2. Add mock tests for Nitrado HTTP success/fail and `download` token format. Keep strict SSRF and token protection.
3. Add robust incremental API `seek` support *after* validation; stay under provider rate limits.
4. Normalize event classes using **anonymized**, verified ADM/RPT grammar from multiple DayZ versions.
5. Add time-zone handling, import timestamps, retention/export controls and admin-only auth before public deployment.
6. Add validated map coordinate transforms and legally licensed terrain imagery for Chernarus/Livonia/Sakhal/Nasdara.
7. Write permissions-checked moderation operations only after explicit human approval flows and server-level tests.

## Non-goals / safety
No client injection, anticheat bypass, unauthorized client memory access, in-game freecam/ESP/teleport, blanket device bans or unverified 'realtime' claims. Console positions typically sample every ~5 minutes. Do not infer live whereabouts.

## Suggested division
- Claude: API security, parser correctness, moderation authorization.
- Gemini: frontend, map math, field validation, bilingual UX.
- Grok: official source verification, third-party interface audit, compatibility matrix.

## Naming
Public project: DayZ Console Observatory. GitHub slug suggestion: `dayz-console-observatory`. Python distribution: `dayz-console-observatory`. Binary: `dayz-observe`.

## v0.4 integration
- `src/dayz_observatory/sync.py` offers read-only whole-file caching based on remote size/mtime and local SHA-256.
- `dayz-observe nitrado SERVICE_ID --dry-run` previews downloads without writing local files.
- `--include-rpt` is opt-in; remote range `seek` is NOT implemented. Never describe log coordinates as live ESP.
- Validate without DayZ: `python -W error::ResourceWarning -m unittest discover -s tests -v`.

## v0.5 watch rules
- `dayz-observe nitrado SERVICE_ID --watch --interval 300` repeatedly calls the existing read-only sync in the foreground.
- Never persist credentials, expose server identifiers in watch output, or silently loosen the minimum 60-second interval.
- Stop after 3 consecutive failed/partial cycles; tests inject fake transports, not real remote tokens.
- Position snapshots remain about 5 minutes apart: a faster poll is not live ESP.

## v0.5.1 evidence rules
- `dayz-observe case PLAYER_ID --out report.json` defaults to aggregate-only output. `--private` intentionally includes identifiable raw records; never attach those to public issues.
- Fingerprints are consistency checks, not proof that a server event is genuine. Preserve explicit limitations of sparse ADM samples.
- Ingest rechecks consumed-prefix SHA-256 even if inode, size and leading bytes did not change. Tests must cover in-place rewrites.
