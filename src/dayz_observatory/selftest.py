"""Offline end-to-end Nitrado API simulation: no credentials and no network."""
from __future__ import annotations
import io
import json
from pathlib import Path
import tempfile
import urllib.parse

from .beta import probe_nitrado
from .nitrado import NitradoClient
from .store import get_quality_report
from .sync import sync_once

SCHEMA = "dayz-observatory-selftest-v1"
_SERVICE = 424242
_USERNAME = "synthetic-host"
_DIRECTORY = f"/games/{_USERNAME}/noftp/dayzxb/config"
_NAME = "SYNTHETIC.ADM"
_REMOTE = _DIRECTORY + "/" + _NAME
_TOKEN = "OFFLINE_FIXTURE_NO_AUTH"
_SAMPLE = (
    'AdminLog started on 2026-10-15 at 12:00:00\n'
    '12:01:00 | Player "SYNTHETIC_TESTER" (id=SYNTHETIC_ID_001 pos=<120, 150, 5>)\n'
).encode("utf-8")
_APPEND = (
    '12:06:00 | Player "SYNTHETIC_TESTER" (id=SYNTHETIC_ID_001 pos=<140, 170, 5>)\n'
).encode("utf-8")


class SelfTestError(RuntimeError):
    """Safe error that excludes credentials and remote service information."""


class _Response:
    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)

    def read(self, count: int = -1):
        return self._stream.read(count)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._stream.close()
        return False


class _SyntheticTransport:
    """Strict allowlist HTTP substitute installed on the real NitradoClient."""

    def __init__(self):
        self.content = _SAMPLE
        self.revision = 1
        self.api_requests = 0
        self.download_requests = 0

    @staticmethod
    def _json(value: dict):
        return _Response(json.dumps(value).encode("utf-8"))

    def open(self, request):
        parsed = urllib.parse.urlsplit(request.full_url)
        query = urllib.parse.parse_qs(parsed.query)
        auth = request.get_header("Authorization")
        if request.get_method() != "GET" or parsed.scheme != "https":
            raise SelfTestError("Offline transport rejected a request method or scheme")
        if parsed.hostname == "api.nitrado.net":
            if auth != "Bearer " + _TOKEN:
                raise SelfTestError("Offline API authentication contract failed")
            self.api_requests += 1
            base = f"/services/{_SERVICE}/gameservers"
            if parsed.path == base:
                return self._json({"data": {"gameserver": {"game": "dayzxb", "username": _USERNAME}}})
            if parsed.path == base + "/file_server/list" and query.get("dir") == [_DIRECTORY]:
                return self._json({"data": {"entries": [
                    {"name": _NAME, "path": _REMOTE, "type": "file",
                     "size": len(self.content), "modified_at": self.revision}
                ]}})
            if parsed.path == base + "/file_server/download" and query.get("file") == [_REMOTE]:
                return self._json({"data": {"token": {
                    "url": "https://files.nitrado.net/offline-fixture",
                    "token": "synthetic-one-use"
                }}})
        if parsed.hostname == "files.nitrado.net" and parsed.path == "/offline-fixture":
            if auth is not None or query.get("token") != ["synthetic-one-use"]:
                raise SelfTestError("Account token leaked to the file host")
            self.download_requests += 1
            return _Response(self.content)
        raise SelfTestError("Offline transport rejected an unknown endpoint")


def run_selftest() -> dict:
    """Exercise real client, sync and SQLite code with a fake local HTTP transport."""
    transport = _SyntheticTransport()
    api = NitradoClient(token=_TOKEN)
    api._open = transport.open  # Offline transport: network opener is never called.
    with tempfile.TemporaryDirectory(prefix="dayz-selftest-") as directory:
        root = Path(directory)
        output, db = root / "logs", root / "events.db"
        probe = probe_nitrado(api, _SERVICE)
        if not probe["xbox_service_detected"] or probe["adm_files_visible"] != 1:
            raise SelfTestError("Synthetic metadata probe failed")
        if transport.download_requests:
            raise SelfTestError("A metadata-only probe unexpectedly downloaded logs")

        preview = sync_once(api, _SERVICE, output=output, db=db, dry_run=True)
        if preview["selected_files"] != 1 or output.exists() or db.exists():
            raise SelfTestError("Synthetic dry-run modified local data")

        first = sync_once(api, _SERVICE, output=output, db=db)
        if first["errors"] or first["downloaded"] != 1 or first["files"][0]["new_events"] != 1:
            raise SelfTestError("Initial synthetic ADM sync failed")

        repeat = sync_once(api, _SERVICE, output=output, db=db)
        if repeat["errors"] or repeat["cached"] != 1 or repeat["downloaded"] != 0:
            raise SelfTestError("Log cache verification failed")
        if repeat["files"][0]["new_events"] != 0 or transport.download_requests != 1:
            raise SelfTestError("Idempotent ingest verification failed")

        transport.content += _APPEND
        transport.revision += 1
        updated = sync_once(api, _SERVICE, output=output, db=db)
        quality = get_quality_report(db, str(_SERVICE))
        if (updated["errors"] or updated["downloaded"] != 1 or
                updated["files"][0]["new_events"] != 1 or
                quality["events"] != 2 or quality["position_observations"] != 2):
            raise SelfTestError("Atomic log append or SQLite history verification failed")

    return {
        "schema": SCHEMA,
        "result": "passed",
        "tests": {
            "xbox_metadata": True, "metadata_only_probe": True,
            "dry_run": True, "signed_download": True,
            "cached_sync": True, "no_duplicate_events": True,
            "log_append": True, "credential_separation": True
        },
        "synthetic_downloads": transport.download_requests,
        "synthetic_positions_imported": 2,
        "used_real_network": False,
        "used_real_server": False,
        "notes": "Synthetic fixture only; live Nitrado Xbox compatibility remains unverified."
    }
