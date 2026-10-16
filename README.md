# DayZ Console Observatory

**A private, local browser workspace for DayZ Xbox / Microsoft Store community-server evidence.** Free, open source (MIT), independent of Bohemia, Nitrado and Microsoft.

[Español](README.es.md) · [Start here](docs/GUI_GUIDE.md) · [AI/developer map](AGENTS.md) · [Documentation index](docs/INDEX.md)

> **v0.8.0 — experimental.** The app, historical ADM parser, GUI workflows and synthetic Nitrado tests run without installing DayZ. **Live Nitrado Xbox compatibility remains unverified**; no publisher-approved spectator, ESP, teleport or invisibility API is included.

## Open it without a command line

**Windows:** Install Python 3.10 or newer, extract the complete repository, then **double-click `START_HERE.cmd`**. Your browser opens the local application.

**macOS/Linux:** From the extracted folder, run `python3 launcher.py`. No pip packages, Nitrado account or external network are required for this workspace.

**In the browser:**
1. Choose **Launch interactive demo** for clearly labeled *synthetic* data. Demo records are kept separate from your own.
2. Use **Choose .ADM file → Import file** to analyze a server administrator log without a terminal. Repeat after the ADM grows to add new observations (8 MiB upload limit).
3. Review recorded positions, player timelines, event classifications and time-window incident clusters. Nothing here represents current player location.

The browser UI runs exclusively on `127.0.0.1`. Files and SQLite are stored under your user's private application-data folder (Windows `%LOCALAPPDATA%\DayZConsoleObservatory`; other systems `~/.local/share/DayZConsoleObservatory`). **Do not expose its port**: detailed read-only endpoints have no remote authentication. No files are sent to our developers or third-party telemetry.

## What the project does and does not do

| Available and offline-tested | Not provided / requires external validation |
| --- | --- |
| One-click launcher, browser upload, isolated demo | Standalone Windows executable (Python must be installed) |
| ADM log parser, persistent SQLite, replay of recorded positions | Continuous real-time ESP, actual map terrain |
| Player and incident reviews, safe aggregate exports | In-game spectator/freecam, teleport, invisibility |
| Integrity checks, backups, explicit local retention | Automatic moderation or hardware-native bans |
| Experimental read-only Nitrado API client and foreground polling | Real Xbox/Nitrado service compatibility (still untested) |

ADM coordinates are discrete historical samples, normally around five minutes apart. Sparse samples cannot establish movement between observations or justify automated accusations. The graph is a schematic coordinate plane, not licensed DayZ map imagery.

## Advanced, optional developer/server-owner commands

```bash
python -m pip install -e .
dayz-observe selftest
dayz-observe doctor --db observatory.db
dayz-observe --help
```

Authorized Nitrado owners may use `dayz-observe nitrado THEIR_SERVICE_ID --probe` with their token in a local environment variable. See [Nitrado field validation](docs/NITRADO_VALIDATION.md); **never upload tokens, raw ADM/RPT logs, player IDs or private databases**. The GUI does **not** ask for Nitrado credentials.

## Collaborate / research

- [Module and test navigation for AI agents](AGENTS.md) · [machine-readable index](project-index.json).
- [Architecture, setup, privacy and research](docs/INDEX.md).
- [Code and contribution guidelines](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md).
- [Issue tracker](https://github.com/chrishotza/DayZConsoleObservatory/issues). No community/public outreach or official cooperation has been initiated as part of this release.

**Trademark disclaimer:** DayZ belongs to Bohemia Interactive. No game files, proprietary terrain tiles, client cheats or anti-cheat bypass tools are distributed.
