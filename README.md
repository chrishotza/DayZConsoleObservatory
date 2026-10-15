# DayZ Console Observatory

**Open-source, local-first observability for DayZ Microsoft Store PC / Xbox community servers.**

Not a cheat or an in-game admin mod. Designed for the Microsoft/Xbox version where Steam Workshop mods are unavailable.

> Status: **v0.2 / early development / read-only**. Offline tests pass; the Nitrado connector **has not been validated with a real owner's token or live DayZ Xbox service**. Do not deploy for production moderation without verification.

## What works today

- Parse documented DayZ ADM formats: positions, connections, disconnections, simple combat/build markers and unknown lines.
- Correct coordinate convention: `pos=<X, Z, altitude>`; optional hyphen before `pos=`.
- SQLite persistence, independent servers, byte-offset deduplication, partial lines, truncation, basic log rotation and midnight transitions.
- Local dashboard at `127.0.0.1`, showing the most recent **historical** player positions on a *schematic coordinate plot*, filterable administrative events, and a **player investigation selector** with session timeline. **This is not a textured map nor a live ESP overlay.**
- Read-only per-player incident export via `dayz-observe investigate PLAYER_ID --db observatory.db --server default`. It reconstructs connect/disconnect *log sessions*, explicitly flags missing evidence, and never claims a player is currently online.
- Experimental read-only Nitrado connection for `dayzxb`: game service metadata, directory listing and ADM download using OAuth bearer token.
- No required third-party Python packages for local operation.

### Known limitations

- ADM player lists are normally sampled about once every five minutes, not continuously. Polling a log faster **does not** increase game sampling frequency.
- Most logs contain server-local timestamps with no explicit timezone; the UI does **not** claim UTC or calculate a misleading age.
- Log classification is deliberately conservative. Unknown lines are kept for future parser development, but not all damage/build log grammars are supported yet.
- The dashboard is a coordinate plane, not licensed DayZ terrain imagery. Mapping profiles including Nasdara will need verified transforms and legally reusable tiles.
- The Nitrado adapter currently downloads the newest ADM in full; partial `seek` optimization and real-host compatibility tests are pending.
- Truncation and inode/prefix checks cover common rotation scenarios; an overwritten log with identical prefix, inode and length is not detectable by this v0.1 mechanism.
- No ban/whitelist writes, online player state modification, ESP-in-game, free camera, invisibility, or teleports. This project must not claim to provide undocumented console APIs.

Para instrucciones en español, consulta [README.es.md](README.es.md).

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
dayz-observe nitrado 12345678 --out private-logs --db observatory.db
# View a specific server ID, e.g. one matching your Nitrado service ID:
dayz-observe dashboard --server 12345678 --db observatory.db
```

The experimental adapter expects the `dayzxb` Nitrado game type and reads its `config` folder. If your host provides another format or download CDN domain, **do not bypass the safety check**: open an issue with redacted endpoint metadata.

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

1. **v0.2 (delivered locally + to be pushed):** Player/session timeline for offline incident review, player filter in dashboard, CLI/HTTP query, offline tests.
2. **v0.3:** Validate Nitrado adapter with real-owner testing and fixtures; add rate-limit recovery and safe partial download (`seek`), data retention controls.
3. **v0.4:** Map overlays using properly licensed tiles per terrain (Chernarus, Livonia, Sakhal, Nasdara), with exact alignment tests.
4. **v0.5:** Optional role-protected server-management actions supported by Nitrado, with explicit confirmation, audit logging and test-only modes.

## References

- Bohemia DayZ administration logs: https://community.bistudio.com/wiki/DayZ:Administration_Logs
- DayZ 1.29: https://dayz.com/article/game-update/DayZ-Update-129
- Nitrado developer documentation: https://doc.nitrado.net/
- Open-source example to study independently: https://github.com/Sat727/Dayz-Console-Killfeed (MIT; no source code copied into DayZ Console Observatory).

## License and disclaimer

MIT. Independent community project. Not affiliated with or endorsed by Bohemia Interactive, Xbox, Microsoft, Nitrado or BattlEye. DayZ game assets and trademarks belong to their owners. No proprietary map images or game code are distributed here.
