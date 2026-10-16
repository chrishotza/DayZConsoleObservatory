# AI_START_HERE · DayZ Console Observatory v0.8.0

**Read this first (target: under 1 minute).** Source: `src/dayz_observatory/`. `project-index.json` is the machine-readable map. Do not read the whole repo before choosing a task.

## Context in 4 sentences

This is a **local-first, browser-based** admin-log observability tool for DayZ Microsoft/Xbox. It parses historical ADM events into SQLite, shows a local timeline/map, and exports evidence; a real Xbox Nitrado service is **not yet validated**. There is **no** authorized in-game ESP, teleport, invisibility or freecam. Synthetic test fixtures are not live data.

## Fast task router

| Intent | First file(s) | Tests |
| --- | --- | --- |
| Browser workflows, demo, ADM upload | `server.py`, `web/app.js`, `web/index.html` | `test_browser_import.py`, `test_http.py`, `test_ui_contract.py` |
| Windows double-click launch | `launcher.py`, `START_HERE.cmd` | `test_launcher.py`, Windows GitHub Actions |
| Parse event grammar | `parser.py` | `test_parser.py` |
| SQLite append, rotation, quality | `store.py` | `test_store.py`, `test_windows_file_identity.py` |
| Player investigations | `investigate.py`, `casebook.py` | `test_investigate.py`, `test_casebook.py` |
| Temporal incidents | `incidents.py` | `test_incidents.py` |
| Nitrado GET API, download | `nitrado.py`, `sync.py`, `watch.py` | `test_nitrado.py`, `test_sync.py`, `test_watch.py` |
| Offline reproducible test | `selftest.py`, `beta.py` | `test_selftest.py`, `test_beta.py` |
| SQLite backup, retention, doctor | `maintenance.py` | `test_maintenance.py`, `test_maintenance_cli.py` |
| CLI and version | `cli.py`, `pyproject.toml`, `__init__.py` | focused CLI tests |

## Verify before editing

```bash
python -m unittest discover -s tests -v
python launcher.py --check
python -m compileall -q src tests launcher.py
```

GitHub Actions also tests Linux Python 3.10/3.12/3.13 and Windows 3.12. **A passing test does not validate real Nitrado behavior.**

## Security invariants

1. The HTTP server binds only `127.0.0.1`; no CORS. Browser mutations require same-Origin, exact Host and a custom header. No remote/admin authentication is implemented. Never expose the port.
2. Demo uses `__dayz_synthetic_demo__`, separate from local records; the UI must make this visible. User uploads are bounded at 8 MiB, kept on disk locally and never forwarded to a network service.
3. Default case and incident exports are aggregate-only. Private identity, coordinates or raw ADM/RPT must never appear in public issues. Fingerprints are consistency checks, not evidence authentication.
4. ADM timestamps use the server clock, timezone often unknown; 5-minute positions do **not** imply live trajectories or guilt. No automatic punishment.
5. The Nitrado connector is experimental GET-only with strict signed-download hosts; remote range `seek` is not implemented.
6. Game-state modification requires a formally authorized Bohemia/platform interface. Do not claim permission, affiliation, or features not implemented.
7. No unsolicited community/publisher outreach until the repo owner approves it.

## Documentation navigation

Read [docs/INDEX.md](docs/INDEX.md) for a human-oriented subject map, [docs/GUI_GUIDE.md](docs/GUI_GUIDE.md) for onboarding, [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md) for evidence gates. Use [CHANGELOG.md](CHANGELOG.md) to check versioned claims. No credentials or personal data in commits.

## Delivery checklist

Implement code, add reproducible regression tests, update user-visible English and Spanish guidance, and verify the **actual HEAD** GitHub Actions result on all supported environments before claiming success.
