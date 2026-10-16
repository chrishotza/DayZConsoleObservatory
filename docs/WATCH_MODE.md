# Foreground monitoring: watch mode

**Status: offline-tested, awaiting a consenting Nitrado Xbox server owner.** No access to in-game player state or client modifications is implemented.

## Recommended order

1. Run the offline `dayz-observe selftest` first (no account, game, or network).
2. On your own Nitrado account, verify `dayz-observe nitrado YOUR_SERVICE_ID --probe` in private.
3. Preview two cycles: `dayz-observe nitrado YOUR_SERVICE_ID --watch --dry-run --cycles 2`.
4. To import ADM locally, run `dayz-observe nitrado YOUR_SERVICE_ID --watch --interval 300` in your terminal; Ctrl+C stops it.
5. Start the local dashboard in a separate terminal with the same `--db` and `--server` setting as your synchronization.

**Token handling:** set `NITRADO_TOKEN` only on your own computer. Never put it in a command captured for posting, shared screenshots, issues or Git history. Never share ADM/RPT files containing players' identifiers or locations.

## Boundaries and failure behavior

- Minimum interval 60 seconds, default 300 seconds, maximum 86400 seconds; interval measured from the start of consecutive syncs.
- Three consecutive cycles with errors or partial errors halt the process. The tool does **not** retry forever after repeated 401, 429, or 503 responses.
- Output is aggregate JSON only: cycle, status, number of selected/downloaded/cached files and error count. Errors are categorical; raw API exception messages are omitted.
- This uses the current complete-file cache and download path, **not** remote byte-range `seek`.
- Existing `sync_once` can retrieve metadata and download logs; because ADM player samples usually occur every five minutes, the watch interval cannot increase the sampling frequency.
- The local SQLite database and downloaded logs remain **sensitive**: no automatic upload or telemetry occurs. The UI is loopback-only, not authenticated for remote access.
- This mode does not provide an ESP overlay, spectator/freecam, teleportation, invisibility or other in-game administrator rights.

## What is independently verifiable

- ADM fields and approximately five-minute player snapshots: https://community.bistudio.com/wiki/DayZ:Administration_Logs
- Nitrado API documentation and 429/503 errors: https://doc.nitrado.net/
- Community need for authorized in-game administration: https://feedback.bistudio.com/T197558
- Policy on Xbox/Microsoft Store modding: https://dayz.com/faq

If a server owner's diagnostic differs, investigate only with redacted response shapes and sanitized error classes. Do not relax host validation to accommodate an unexpected external download URL.
