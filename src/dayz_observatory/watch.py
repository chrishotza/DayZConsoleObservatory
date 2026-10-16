"""Rate-bounded, read-only foreground Nitrado polling; aggregate-only output.

ADM positions normally remain 5-minute snapshots, regardless of polling.
No player, server, file or token identities are forwarded to the callback.
"""
from __future__ import annotations

import time
from typing import Any, Callable

MIN_INTERVAL = 60
DEFAULT_INTERVAL = 300
MAX_INTERVAL = 86400
MAX_FAILURES = 3


def watch_foreground(
    api: Any,
    service_id: int,
    *,
    output: str,
    db: str,
    server: str | None = None,
    interval: int = DEFAULT_INTERVAL,
    max_cycles: int | None = None,
    max_files: int = 3,
    include_rpt: bool = False,
    dry_run: bool = False,
    sync_fn: Callable[..., dict] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    monotonic_fn: Callable[[], float] | None = None,
    on_cycle: Callable[[dict], None] | None = None,
) -> dict:
    """Sync at most once per interval, until Ctrl+C or max_cycles.

    Three consecutive failed or partial cycles halt repeated remote requests.
    Callback output is allowlisted and contains no individual identifiers.
    """
    if isinstance(interval, bool) or not isinstance(interval, int) or not MIN_INTERVAL <= interval <= MAX_INTERVAL:
        raise ValueError("Watch interval must be an integer between 60 and 86400 seconds")
    if max_cycles is not None and (isinstance(max_cycles, bool) or not isinstance(max_cycles, int) or max_cycles < 1):
        raise ValueError("Watch cycles must be a positive integer")
    if isinstance(max_files, bool) or not isinstance(max_files, int) or not 1 <= max_files <= 20:
        raise ValueError("Watch max_files must be between 1 and 20")
    if isinstance(service_id, bool) or not isinstance(service_id, int) or service_id <= 0:
        raise ValueError("Service ID must be positive")
    if sync_fn is None:
        from .sync import sync_once
        sync_fn = sync_once
    sleep = sleep_fn if sleep_fn is not None else time.sleep
    clock = monotonic_fn if monotonic_fn is not None else time.monotonic

    completed = consecutive_failures = 0
    while max_cycles is None or completed < max_cycles:
        started = clock()
        try:
            result = sync_fn(api, service_id, output=output, db=db, server=server,
                             max_files=max_files, include_rpt=include_rpt,
                             dry_run=dry_run, force=False)
            if not isinstance(result, dict):
                raise ValueError("Unexpected synchronization result")
            errors = result.get("errors")
            if not isinstance(errors, list):
                raise ValueError("Unexpected error report")
            report = {
                "cycle": completed + 1,
                "status": "partial" if errors else "ok",
                "downloaded": _count(result.get("downloaded")),
                "cached": _count(result.get("cached")),
                "selected_files": _count(result.get("selected_files")),
                "errors": len(errors),
                "dry_run": bool(dry_run),
            }
        except (OSError, ValueError, RuntimeError) as exc:
            # Exception messages may contain remote service paths or URLs.
            report = {
                "cycle": completed + 1, "status": "error",
                "downloaded": 0, "cached": 0, "selected_files": 0,
                "errors": 1, "dry_run": bool(dry_run),
                "error_category": _error_category(exc),
            }
        completed += 1
        consecutive_failures = consecutive_failures + 1 if report["status"] != "ok" else 0
        if on_cycle is not None:
            on_cycle(report)
        if consecutive_failures >= MAX_FAILURES:
            return {"status": "stopped_after_errors", "cycles": completed}
        if max_cycles is not None and completed >= max_cycles:
            break
        sleep(max(0.0, float(interval) - max(0.0, clock() - started)))
    return {"status": "completed", "cycles": completed}


def _count(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def _error_category(exc: BaseException) -> str:
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, OSError):
        return "network_or_file"
    if isinstance(exc, ValueError):
        return "invalid_response"
    return "remote_service"
