# Testing without owning or running DayZ

You **do not need to install or launch DayZ** for offline development of the log parser, SQLite store, local dashboard, or mocked Nitrado HTTP adapter.

## Offline confidence

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
dayz-observe ingest samples/SYNTHETIC_dayz.ADM --db observatory.db
dayz-observe dashboard --db observatory.db
```

Open http://127.0.0.1:8765. All samples in the repository are synthetic; passing tests does **not** prove compatibility with a live service or that particular events are emitted for every server configuration.

## Online acceptance requires a volunteer server administrator

1. Confirm the service is DayZ's Xbox/Microsoft ecosystem and that the owner can view ADM logs in their hosting panel.
2. On the owner's machine, create a narrowly scoped Nitrado token. **Do not paste tokens or unredacted logs into GitHub issues or chats.**
3. Run `dayz-observe nitrado YOUR_SERVICE_ID --list-only` and compare the displayed file names to the hosting panel. Do not send the token to contributors.
4. If that works, run the read-only log download; redacted event samples are enough to improve the parser.
5. Confirm which event fields are present and how recent data appears. Measure the time from game event, to file update, to dashboard update.
6. Review console and Microsoft Store version compatibility after game/hosting updates. Exercise this on a test server before production.

Use GitHub Issues to record *sanitized* pass/fail observations, API HTTP status codes, server `game` identifiers and missing event patterns. **Do not** upload live player identifiers, devices, IP addresses, passwords or access tokens.

## Safe claims

- Offline parser and UI functionality can be tested locally without DayZ.
- A real Nitrado deployment still needs an owner with a valid server/token.
- No test in this repository establishes live ESP, invisibility, teleport or an in-game spectator camera on Microsoft/Xbox DayZ.
