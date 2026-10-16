# Player case exports and evidence provenance (v0.5.1)

**Purpose:** locally review a player's **historical** ADM records, and optionally share only aggregate statistics without exposing identities or coordinates.

## Example

After importing ADM files into your own database:

```powershell
dayz-observe case PLAYER_ID --db observatory.db --server YOUR_SERVICE_ID --out private-share-summary.json
```

The default export is **aggregate-only** and deliberately excludes player IDs/names, exact timestamps, coordinates, source paths, raw logs and line fingerprints. It is suitable for voluntary technical feedback, but **not** a complete forensic incident transcript. Counts of events linked to an individual may still be sensitive in small communities; review before publishing.

For local review **only**, request full evidence explicitly:

```powershell
dayz-observe case PLAYER_ID --db observatory.db --server YOUR_SERVICE_ID --out private-evidence.json --private
```

The private JSON includes raw lines, names, identifiers, timestamps, coordinates, source path, byte offset and source generation. Never publish it or upload it to a public issue. The destination is created with owner-only permissions where supported; existing files and symlinks are not overwritten. Both modes print only a small, non-identifying confirmation to the terminal.

## Interpretation

- Every private record includes a **repeatable SHA-256 fingerprint of `[path,generation,byte_offset,raw]`**. This can reveal modification of the exported fields, but is **not** server-authenticated proof or a chain-of-custody guarantee.
- `truncated=true` signals that the requested event limit omitted some matching records. `matched_event_count` is the count in the current database, not the complete game-server history.
- Events are linked only if the parser recognized the player's stable ID. Nearby combat, construction and death logs may remain unlinked. Unknown lines and missing connection/disconnection records reduce completeness.
- Do not infer live online presence, movement between 5-minute snapshots, speed cheating or intent from an exported case.
- Avoid automated punishments: human review and independent evidence are required.
- Database and local downloads remain sensitive even if a **separate aggregate report** is safe to share.

## Record integrity protection

v0.5.1 also checks the SHA-256 of **every previously consumed log byte range on every ingest**. This catches same-inode/same-size in-place rewrites (as well as atomic replacements), creating a new generation rather than treating rewritten lines as an append. It increases disk reading in proportion to already-ingested data, trading some performance for evidence correctness. Hashes still cannot prove the upstream logs are authentic.

Live Nitrado compatibility remains unverified without a consenting community-server owner.
