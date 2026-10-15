"""Conservative, one-shot, read-only Xbox/Nitrado log synchronizer."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any
from .nitrado import NitradoClient, NitradoError
from .store import ingest

STATE_FILE = ".dayz-sync-state.json"
MAX_STATE_BYTES = 1024 * 1024

def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(256 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _remote_signature(entry: dict[str, Any]) -> dict[str, str] | None:
    size, modified = entry.get("size"), entry.get("modified_at")
    if isinstance(size, bool) or not isinstance(size, (int, str)):
        return None
    if isinstance(modified, bool) or not isinstance(modified, (int, float, str)):
        return None
    try:
        numeric_size = int(size)
    except (ValueError, TypeError):
        return None
    if numeric_size < 0 or not str(modified).strip():
        return None
    return {"size": str(numeric_size), "modified_at": str(modified)}

def _read_state(path: Path, *, service_id: int) -> dict[str, Any]:
    if path.is_symlink():
        raise NitradoError("Refusing symlink sync state")
    if not path.exists():
        return {}
    if not path.is_file() or path.stat().st_size > MAX_STATE_BYTES:
        raise NitradoError("Invalid or oversized local sync state")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {}
    if not isinstance(raw, dict) or raw.get("service_id") != service_id:
        return {}
    return raw.get("entries") if isinstance(raw.get("entries"), dict) else {}

def _write_state(path: Path, service_id: int, entries: dict[str, Any]) -> None:
    if path.is_symlink():
        raise NitradoError("Refusing symlink sync state")
    payload = json.dumps({"format": 1, "service_id": service_id, "entries": entries},
                         sort_keys=True, indent=2).encode("utf-8")
    if len(payload) > MAX_STATE_BYTES:
        raise NitradoError("Sync state exceeds safety limit")
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".dayz-state-",
                                         suffix=".part", delete=False) as handle:
            tmp = handle.name
            if os.name == "posix":
                os.fchmod(handle.fileno(), 0o600)
            handle.write(payload)
        os.replace(tmp, path)
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)

def _order(entry: dict[str, Any]) -> tuple[int, str, str]:
    stamp = entry.get("modified_at")
    if isinstance(stamp, (int, float)) and not isinstance(stamp, bool):
        sortable = f"{int(stamp):020d}"
    else:
        sortable = str(stamp or "")
    return (int(stamp is not None), sortable, str(entry.get("name") or ""))

def sync_once(api: NitradoClient, service_id: int, *, output: str | Path,
              db: str | Path, server: str | None = None, max_files: int = 3,
              include_rpt: bool = False, dry_run: bool = False,
              force: bool = False) -> dict[str, Any]:
    """Mirror recent logs, cache whole-file downloads, and ingest ADM locally.

    The dry run only calls metadata endpoints and does not create local files.
    Cached files are still re-ingested if the SQLite DB was deleted or reset.
    """
    service_id = api._service_id(service_id)
    if not isinstance(max_files, int) or isinstance(max_files, bool) or not 1 <= max_files <= 20:
        raise ValueError("max_files must be between 1 and 20")
    directory, info = api.discover_log_directory(service_id)
    candidates = api.list_logs(service_id, directory)
    allowed = (".adm", ".rpt") if include_rpt else (".adm",)
    candidates = [e for e in candidates if str(e.get("name", "")).lower().endswith(allowed)]
    selected = sorted(candidates, key=_order, reverse=True)[:max_files]
    root = Path(output).expanduser().resolve() / str(service_id)
    state_path = root / STATE_FILE
    prior = {} if force or not root.exists() else _read_state(state_path, service_id=service_id)
    outcome: dict[str, Any] = {
        "service_id": service_id, "game": info.get("game"), "server": server or str(service_id),
        "mode": "dry-run" if dry_run else "sync", "available_files": len(candidates),
        "selected_files": len(selected), "downloaded": 0, "cached": 0, "files": [], "errors": []
    }
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
    for item in selected:
        name, remote = item.get("name"), item.get("path")
        if (not isinstance(name, str) or not isinstance(remote, str)
                or remote != directory.rstrip("/") + "/" + name
                or not name.lower().endswith(allowed)
                or name in (".", "..") or "/" in name or "\\" in name):
            outcome["errors"].append("Unsafe remote log metadata rejected")
            continue
        path = root / name
        if path.is_symlink():
            outcome["errors"].append(f"Refusing symlink destination for {name}")
            continue
        signature = _remote_signature(item)
        cached = prior.get(name) if isinstance(prior.get(name), dict) else None
        valid_cache = (not force and signature is not None and cached is not None
                       and cached.get("remote") == remote and cached.get("signature") == signature
                       and path.is_file() and path.stat().st_size == int(signature["size"])
                       and cached.get("sha256") == _digest(path))
        report: dict[str, Any] = {"name": name, "action": "cached" if valid_cache else "download",
                                  "remote_metadata": signature is not None}
        if dry_run:
            outcome["files"].append(report)
            continue
        try:
            if not valid_cache:
                api.download_log(service_id, remote, path, directory)
                confirmed = signature if signature and path.stat().st_size == int(signature["size"]) else None
                prior[name] = {"remote": remote, "signature": confirmed, "sha256": _digest(path)}
                outcome["downloaded"] += 1
            else:
                outcome["cached"] += 1
            if name.lower().endswith(".adm"):
                imported = ingest(db, path, outcome["server"])
                report["new_events"] = imported["new_events"]
                report["generation"] = imported["generation"]
                report["rotated"] = imported["rotated"]
            _write_state(state_path, service_id, prior)
            outcome["files"].append(report)
        except (NitradoError, OSError, ValueError) as exc:
            outcome["errors"].append(f"{name}: {type(exc).__name__}")
    return outcome
