# Owner-only Nitrado Xbox field validation

**Experimental, not yet validated with a real Xbox community server.** You do not need DayZ installed to run the project’s offline tests.

Never share your Nitrado token, service-specific logs, player identifiers, RPT files, or other private information publicly.

## Safe first steps (PowerShell)

```powershell
python -m pip install -e .
python -W error::ResourceWarning -m unittest discover -s tests -v
$env:NITRADO_TOKEN = "<your-own-Nitrado-token>"
dayz-observe nitrado 12345678 --list-only
dayz-observe nitrado 12345678 --dry-run --out private-logs --db observatory.db
```

Replace the example service ID locally. First verify that Nitrado returns the expected `dayzxb` server and ADM file metadata. Do not give the token to any developer or AI.

After the **read-only preview** succeeds:

```powershell
dayz-observe nitrado 12345678 --out private-logs --db observatory.db
dayz-observe nitrado 12345678 --out private-logs --db observatory.db
dayz-observe audit --db observatory.db --server 12345678
```

The second sync should skip a download only if Nitrado supplied usable size and modified-time metadata and local SHA-256 still matches. Otherwise re-downloading is intentional. To include older rotated ADM files use `--max-files 8` (max 20). Force verification with `--force`. RPT files are skipped unless `--include-rpt` is explicitly set.

## Share only sanitized results

Report: HTTP status, whether listing worked, downloaded/cached counts, rotation observed, whether entries were imported. Never paste logs, player IDs, signed URLs, device IDs or tokens. A 429/503 may require a later retry.

Polling often **does not** improve the game engine's ~5-minute position logging interval. The dashboard displays historical evidence, not live player tracking or in-game ESP, free camera, invisibility or teleportation.

This is an independent community project with no official affiliation or authorization from Bohemia, Microsoft/Xbox, Nitrado or BattlEye.
