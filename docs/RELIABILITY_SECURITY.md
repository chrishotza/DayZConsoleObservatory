# Reliability, evidence integrity and security model

DayZ Console Observatory is an **unofficial, read-only** desktop-local tool. It does not control game entities, teleport players, bypass anti-cheat, or use undocumented DayZ APIs.

## Trust boundaries

```text
Nitrado HTTPS (service owner token) -> validated DayZ Xbox service metadata
    -> approved log listing -> restricted single-file download URL
    -> atomic local file -> byte-offset ADM parser -> SQLite
    -> loopback-only HTTP UI (127.0.0.1)
```

No game installation or service credentials are needed to run tests. Nitrado interactions still require verification on a consenting server owner's account.

### Remote access

- Bearer token is read from `NITRADO_TOKEN`, never stored in source or passed to the file-download host.
- **No HTTP redirects are followed**, either for the account API or for signed log downloads. This is intentional: the default redirect behavior may expose authentication data to another host. If a legitimate Nitrado deployment starts requiring redirects or a separate CDN, report redacted endpoint metadata so the allowed-host policy can be revised safely.
- Download URLs require HTTPS, a host in the explicitly allowlisted Nitrado domains and no embedded HTTP credentials or fragment.
- The downloaded filename must be an `.ADM` or `.RPT` file directly inside the discovered DayZ Xbox log directory. Relative path traversal and nested directories are rejected.
- API JSON responses are capped at 2 MiB; downloaded logs are capped at 50 MiB.
- Downloads use an atomic temporary file in the destination directory. A failed download preserves the previously downloaded file; the partial temporary file is deleted.
- HTTP errors do not include request URLs or tokens in error messages. HTTP 429 and 503 permit only one bounded JSON metadata GET retry, honoring numeric Retry-After up to 5 seconds. Signed file downloads are not retried automatically.

### Local application

- The dashboard binds to `127.0.0.1` only. Do not reverse-proxy the API onto the internet; it is **not authenticated**.
- CSP, `no-store`, `nosniff` and a small static route allowlist restrict the browser surface. The UI assigns text using `textContent` rather than inserting raw event strings as HTML.
- Default output logs and SQLite files are excluded from Git via `.gitignore`. ADM/RPT can contain persistent player identifiers. Do not upload live player logs to GitHub or share them in public issues.
- No player bans, device-based actions or other state-modifying endpoints are implemented.

## What tests establish

`python -m unittest discover -s tests -v` runs without network access. The suite covers parser variants, file rotations, partial lines, multi-server isolation, chronology, player sessions, API errors, response limits, URL/path rejection, atomic downloads and a real loopback HTTP server. CI runs on Python 3.10, 3.12 and 3.13.

Passing these tests **does not establish that Nitrado grants the necessary endpoints to every Xbox server, nor that admin records are complete, immediate or unbiased**.

## Interpretation of evidence

- Positions in ADM logs are **historical samples**. Frequent polling cannot increase the game server's position sample frequency.
- The plotted coordinate axes are X (east-west) and Z (north-south); `altitude` is the third recorded component. This is not terrain imagery.
- Timestamps are the game server's wall clock. When the timezone is unknown, do not infer precise latency or UTC.
- A session without a matching `disconnected` line is not proof that a player is online.
- Importing an older log after a newer one must not reorder the displayed player snapshot. Database queries sort dated events by their timestamps rather than ingestion sequence.
- Unknown event grammars are preserved. An absence of events is not evidence that something never occurred.

## Known open problems

1. Live Nitrado permission and host compatibility still need field testing by an authorized server owner.
2. The adapter downloads several recent whole ADM files, avoiding repeated downloads when remote size+mtime and local SHA-256 match. Remote `seek` is not integrated. The remote source could change despite identical metadata, requiring `--force`.
3. Source-file rewrite detection handles inode changes, truncation and prefix changes. Same-size rewrites retaining an identical prefix remain a limitation.
4. No actual in-game spectate, ESP, invisibility, teleport or privileged admin action is exposed by the project.
5. No approved Bohemia, Nitrado, Microsoft/Xbox or BattlEye partnership exists. [An official API proposal](BOHEMIA_ADMIN_API_PROPOSAL.md) is maintained separately and does not itself grant permission.

## Reporting vulnerabilities

Follow [SECURITY.md](../SECURITY.md). Never post real tokens, raw live ADM/RPT data, hardware IDs, IP addresses, or personally identifying information in public issues.
