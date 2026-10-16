# Engineering handoff · DayZ Console Observatory (v0.6.0)

**Purpose:** source-first, local-only analysis for DayZ Microsoft Store PC / Xbox Nitrado community servers. MIT, independent and unaffiliated. Maintain documented limits; do not claim in-game ESP, freecam, invisibility, teleportation or verified live Nitrado integration.

## Minimal entrypoints

- Install offline source: `python -m pip install -e .` (requires Python 3.10+).
- Core tests: `python -W error::ResourceWarning -m unittest discover -s tests -v`.
- Simulated Nitrado transport end-to-end: `dayz-observe selftest` (no credentials, no network).
- Historical sample: `dayz-observe ingest samples/SYNTHETIC_dayz.ADM --db observatory.db`.
- Local dashboard: `dayz-observe dashboard --db observatory.db` (127.0.0.1 only).
- CLI reference: `dayz-observe --help`; then `dayz-observe COMMAND --help`.

## Source navigation by intention

| Task | Source | Safety invariant |
| --- | --- | --- |
| Parse ADM logs | `src/dayz_observatory/parser.py` | Positions are `X,Z,altitude`; unrecognized events must not be invented |
| Import & quality | `store.py` | SQLite isolation, idempotence, complete lines, consumed-prefix SHA-256, no guessed UTC |
| Player timeline | `investigate.py` | No proof of live presence from an open session |
| Individual evidence | `casebook.py` | Aggregate-only by default; private output requires `--private` |
| Temporal incidents | `incidents.py` | Clusters mean time proximity, not causality; cap 2,000 and 48 hours |
| Local REST/UI | `server.py`, `web/` | Bind loopback only, never expose without access control |
| Nitrado transport | `nitrado.py` | GET-only; authenticated requests and signed downloads stay separated |
| Remote sync | `sync.py` | Metadata-based cache, atomic files, RPT opt-in, strict destinations |
| Foreground poll | `watch.py` | Default 300 s, minimum 60 s, 3 consecutive errors halt |
| Anonymous diagnostics | `beta.py`, `selftest.py` | No identifying metadata or hidden telemetry |
| Entrypoints | `cli.py`, `pyproject.toml` | Consistent CLI flags/version and safe default disclosure |

Tests live in `tests/` and run in GitHub Actions for Python 3.10, 3.12 and 3.13. Frontend contract tests use Node if present and static checks otherwise. CI evidence is authoritative; **do not claim passing tests or real-server validation without verifying a completed run**.

## Research/implementation ownership

- **API & security desk:** official Nitrado endpoints, data limits, auth scope, SSRF/redirect boundary, credential handling.
- **Scientific methods desk:** sparse player snapshots, sampling uncertainty and false-positive analysis.
- **Product/UX desk:** local case review, mobile/accessibility, verified coordinate map overlays with legally usable assets.
- **Parser/forensics desk:** sanitized fixtures, precise source provenance, temporal ordering, audit integrity.
- **Open-source quality desk:** license review, PR tests, dependency monitoring, error reproduction and docs consistency.
- **Publisher integration desk:** Bohemia approvals for console in-game admin functions. No API exists in this project to modify live player state.

Claude, Gemini and Grok may contribute independently with explicitly shared evidence; **do not claim a model, plugin, team or publisher was contacted unless a real tool action succeeded**.

## Red lines & verification gates

1. No player names, service IDs, tokens, signed URLs, precise coordinates, private RPT/ADM or full incident reports in public GitHub Issues/PRs.
2. Local identifiers are sensitive. `incidents` and `case` default to aggregate-only reports. `--private` is a deliberate confidential action. Hashes are not server attestations.
3. Never turn anomaly patterns into automated accusations, bans or claims of real-time ESP. Five-minute snapshots do not support live tracking.
4. Remote file range `seek` is not implemented. Nitrado production compatibility remains **unverified** until a consenting server owner tests it.
5. Explicit Bohemia/platform permission and a documented server-side interface are required before any in-game spectator, invisibility or teleport integration.
6. Follow `docs/PRODUCT_STRATEGY.md`, `docs/INCIDENT_INVESTIGATION.md`, `docs/CASE_EVIDENCE.md` and `SECURITY.md` before scope changes.

## Pull request acceptance

- Run all offline tests on source modifications; add a regression for every defect.
- Preserve privacy defaults, service isolation, clock assumptions and exact historical provenance.
- Update English/Spanish docs and `CHANGELOG.md` for visible features.
- Verify the HEAD commit and completed CI run after GitHub writes.
- No unsolicited community or company outreach while the project owner has deferred it.

## v0.7 local data operations

- `maintenance.py`: `doctor` uses read-only SQLite URI and never creates a missing DB.
- `backup` uses SQLite online backup to a new owner-private filename and verifies `PRAGMA quick_check`; never overwrite or print player data.
- `retain` previews by default. Applying requires `--apply --confirm-server` exactly matching `--server`, and an explicit exclusive server-local timestamp cutoff. Unknown timestamps and sync source offsets remain untouched.
- Logical deletion does not securely erase WAL/free pages, private ADM files or backups. Warn users; never market this as guaranteed erasure.
- Never export database backups to public GitHub issues or include identifiers in doctor/retention JSON.
