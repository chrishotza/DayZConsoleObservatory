# DayZ Console Observatory

**Open-source, local-first observability for DayZ Microsoft Store PC / Xbox community servers.**

Not a cheat or an in-game admin mod. Designed for the Microsoft/Xbox version where Steam Workshop mods are unavailable.

> Status: **v0.6.0 / early development / read-only**. Offline tests pass; the Nitrado connector **has not been validated with a real owner's token or live DayZ Xbox service**. Do not deploy for production moderation without verification.

## What works today

- Parse documented DayZ ADM formats: positions, connections, disconnections, simple combat/build markers and unknown lines.
- Correct coordinate convention: `pos=<X, Z, altitude>`; optional hyphen before `pos=`.
- SQLite persistence, independent servers, byte-offset deduplication, partial lines, truncation, basic log rotation and midnight transitions.
- Local dashboard at `127.0.0.1`, showing the most recent **historical** player positions on a *schematic coordinate plot*, filterable administrative events, and a **player investigation selector** with session timeline. **This is not a textured map nor a live ESP overlay.**
- Read-only per-player incident export via `dayz-observe investigate PLAYER_ID --db observatory.db --server default`. It reconstructs connect/disconnect *log sessions*, explicitly flags missing evidence, and never claims a player is currently online.
- Read-only Nitrado sync for `dayzxb`: multiple recent logs, local SHA-256 plus remote size/mtime cache, dry-run, and bounded HTTP 429/503 retry.
- No required third-party Python packages for local operation.

### Known limitations

- ADM player lists are normally sampled about once every five minutes, not continuously. Polling a log faster **does not** increase game sampling frequency.
- Most logs contain server-local timestamps with no explicit timezone; the UI does **not** claim UTC or calculate a misleading age.
- Log classification is deliberately conservative. Unknown lines are kept for future parser development, but not all damage/build log grammars are supported yet.
- The dashboard is a coordinate plane, not licensed DayZ terrain imagery. Mapping profiles including Nasdara will need verified transforms and legally reusable tiles.
- The Nitrado adapter downloads up to three recent ADM logs by default (up to 20 with `--max-files`). It skips unchanged full downloads only when remote size and mtime are usable. **Remote byte-range `seek` is not implemented**. A same-size rewrite with unchanged mtime requires `--force` to detect.
- Local ingestion rechecks the SHA-256 of all previously consumed bytes, including in-place rewrites; the remote Nitrado cache still relies on reported size/mtime unless `--force` is used. A log tampered with upstream before download cannot be independently authenticated.
- No ban/whitelist writes, online player state modification, ESP-in-game, free camera, invisibility, or teleports. This project must not claim to provide undocumented console APIs.

Para instrucciones en español, consulta [README.es.md](README.es.md).

## Community beta: Xbox / Microsoft Store server volunteers wanted

Seeking **3–5 Nitrado community server owners** to field-test our read-only integration. You never need to send us a token, server login, or player logs. You can test without DayZ using `dayz-observe beta-report --db observatory.db`. Owners may optionally test `dayz-observe nitrado YOUR_ID --probe`, which prints only anonymous metadata counts and never downloads logs.

Read the [community beta guide](docs/COMMUNITY_BETA.md) and [submit a beta report](https://github.com/chrishotza/DayZConsoleObservatory/issues/new/choose). Our Nitrado connector still needs independent live-server validation.


## Join the GitHub community

You can contribute without owning DayZ. Run **dayz-observe selftest** to exercise an entirely offline simulated Nitrado service, then visit the [community roadmap](docs/COMMUNITY_ROADMAP.md) for beginner tasks, quality assurance, translations, synthetic parser fixtures and UI improvements. Open an issue or a pull request with sanitized evidence only. Passing selftest is not proof of compatibility with a real Nitrado server.


## Foreground monitoring (experimental)

After the private, read-only metadata probe succeeds, run the **bounded, foreground** monitor from your own terminal:

~~~powershell
$env:NITRADO_TOKEN = "<your-token-on-your-computer>"
dayz-observe nitrado YOUR_SERVICE_ID --watch --dry-run --cycles 2
dayz-observe nitrado YOUR_SERVICE_ID --watch --interval 300
~~~

Watch defaults to **one sync attempt every 300 seconds** (minimum 60), stops after three consecutive failed/partial cycles, and prints only aggregate, non-identifying counts. Ctrl+C stops it. This polling does **not** create live positions or bypass any platform restrictions. Live Xbox/Nitrado service behavior remains unverified. See [watch-mode engineering guide](docs/WATCH_MODE.md).


## Case exports and privacy (v0.5.1)

Use `dayz-observe case PLAYER_ID --db observatory.db --out case-summary.json` to create a **privacy-preserving aggregate report** by default. To include private raw evidence for your own review, explicitly add `--private` and use a separate, non-public filename. Existing files are never overwritten, and private identifiers are not printed to the terminal. See [case evidence guide](docs/CASE_EVIDENCE.md). Same-inode ADM rewrites are now detected using consumed-range SHA-256 checks.

## Temporal incident investigation (v0.6.0)

The new **Incident timeline** in the local dashboard groups imported ADM events by proximity in the **server's local clock**, including context from other players within the same temporal window. It does not claim causal interaction or infer live coordinates.

For a share-safe aggregate JSON report, run:

~~~powershell
dayz-observe incidents 2026-10-15T12:00:00 2026-10-15T12:30:00 --db observatory.db --out summary.json
~~~

Optional `--player-id ID` limits results to time windows containing that player while retaining nearby events from other players. Add `--private` **only for confidential, local review** to include timestamps, identities, coordinates, raw lines and record fingerprints. Import limits are explicit (`truncated=true`), undated events are excluded, and a 48-hour upper bound prevents unbounded queries. See [incident investigation guide](docs/INCIDENT_INVESTIGATION.md).

## Quick start (offline demo)

From the project directory:

```bash
python -m pip install -e .
dayz-observe ingest samples/SYNTHETIC_dayz.ADM --db observatory.db
dayz-observe dashboard --db observatory.db
```

Open **http://127.0.0.1:8765**. The sample contains synthetic players and coordinates.

Review one player from imported records:

```bash
dayz-observe investigate SYNTH_PLAYER_001 --db observatory.db
```

The dashboard also supports selecting a player. Timeline events and sample positions are **observations**, not proof of current presence. An open session means *no disconnection was recorded*, which can also occur when logs are incomplete.

Run all tests:

```bash
python -m unittest discover -s tests -v
```

## Optional Nitrado investigation (read-only)

Requires a Nitrado service that grants access to the DayZ Xbox logs. **Do not post your token or unredacted logs in chat or issues.**

Linux/macOS:

```bash
export NITRADO_TOKEN="<token from your own Nitrado account>"
dayz-observe nitrado 12345678 --list-only
```

Windows PowerShell:

```powershell
$env:NITRADO_TOKEN = "<token from your own Nitrado account>"
dayz-observe nitrado 12345678 --list-only
```

When listing has been validated against your account:

```bash
dayz-observe nitrado 12345678 --dry-run --out private-logs --db observatory.db
dayz-observe nitrado 12345678 --out private-logs --db observatory.db
# View a specific server ID, e.g. one matching your Nitrado service ID:
dayz-observe dashboard --server 12345678 --db observatory.db
```

Read [owner-only field validation](docs/NITRADO_VALIDATION.md). Use `--max-files 8` to include recent rotated files, `--force` to re-download, and `--include-rpt` to explicitly opt in to sensitive RPT logs. The experimental adapter expects the `dayzxb` Nitrado game type and reads its `config` folder. If your host provides another format or download CDN domain, **do not bypass the safety check**: open an issue with redacted endpoint metadata.

## Architecture

```text
[DayZ Microsoft / Xbox dedicated service]
                   |
      [Nitrado API, read only]
       GET metadata + ADM files
                   |
      [Local ingestion / parser]
                   |
             [SQLite]
                   |
       [127.0.0.1:8765 local UI]
       events + recorded coordinates
```

## Roadmap

1. **v0.1–v0.3:** Parser, SQLite, investigation timeline, reliability/security and CI.
2. **v0.4–v0.5 (offline-tested):** Multi-file Nitrado synchronization, bounded foreground polling, simulated end-to-end validation and confidential player case exports.
3. **v0.6 (offline-tested):** Server-local temporal incident clustering, anchored context, aggregate-only and private exports, local timeline UI and API.
4. **Next:** Verify actual Nitrado Xbox responses with a consenting owner, improve parser grammar and add explicit data-retention controls.
5. **Later:** Approved map imagery and any formally authorized in-game moderation/spectator interface.

## References

- Bohemia DayZ administration logs: https://community.bistudio.com/wiki/DayZ:Administration_Logs
- DayZ 1.29: https://dayz.com/article/game-update/DayZ-Update-129
- Nitrado developer documentation: https://doc.nitrado.net/
- Open-source example to study independently: https://github.com/Sat727/Dayz-Console-Killfeed (MIT; no source code copied into DayZ Console Observatory).

## License and disclaimer

MIT. Independent community project. Not affiliated with or endorsed by Bohemia Interactive, Xbox, Microsoft, Nitrado or BattlEye. DayZ game assets and trademarks belong to their owners. No proprietary map images or game code are distributed here.
