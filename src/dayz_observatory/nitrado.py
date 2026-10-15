"""Read-only Nitrado API adapter, limited to DayZ Xbox-hosted services.

No undocumented player control, memory access, game commands, or moderation writes.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.nitrado.net"


class NitradoError(RuntimeError):
    pass


class NitradoClient:
    def __init__(self, token: str | None = None, timeout: int = 30):
        self.token = token or os.environ.get("NITRADO_TOKEN")
        if not self.token:
            raise NitradoError("Set NITRADO_TOKEN in your environment. Never put it in source files.")
        self.timeout = timeout

    def _json(self, path: str, params: dict | None = None) -> dict:
        url = BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
            "User-Agent": "dayz-console-observatory/0.1",
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
                if not isinstance(payload, dict):
                    raise NitradoError("Unexpected API response shape")
                return payload
        except urllib.error.HTTPError as exc:
            raise NitradoError(f"Nitrado API HTTP {exc.code} while reading {path}") from None
        except (OSError, ValueError) as exc:
            raise NitradoError(f"Nitrado API unavailable: {exc.__class__.__name__}") from None

    def gameserver(self, service_id: int) -> dict:
        return self._json(f"/services/{int(service_id)}/gameservers")["data"]["gameserver"]

    def discover_log_directory(self, service_id: int) -> tuple[str, dict]:
        data = self.gameserver(service_id)
        game = str(data.get("game", "")).lower()
        username = str(data.get("username", ""))
        if game != "dayzxb":
            raise NitradoError(f"Expected Microsoft/Xbox DayZ service (dayzxb), got {game!r}")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", username) or username in (".", ".."):
            raise NitradoError("Unexpected gameserver username/path")
        return f"/games/{username}/noftp/dayzxb/config", data

    def list_logs(self, service_id: int, directory: str) -> list[dict]:
        data = self._json(f"/services/{int(service_id)}/gameservers/file_server/list", {"dir": directory})
        entries = data.get("data", {}).get("entries", [])
        result = []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("type") != "file":
                continue
            name = str(entry.get("name", ""))
            if name.lower().endswith((".adm", ".rpt")):
                result.append(entry)
        return result

    def download_log(self, service_id: int, remote_path: str, destination: str | Path, allowed_directory: str) -> Path:
        if not remote_path.startswith(allowed_directory.rstrip("/") + "/"):
            raise NitradoError("Refusing file outside the discovered DayZ Xbox log directory")
        if not remote_path.lower().endswith((".adm", ".rpt")):
            raise NitradoError("Refusing non-log file")
        response = self._json(f"/services/{int(service_id)}/gameservers/file_server/download", {"file":remote_path})
        token_info = response.get("data", {}).get("token", {})
        url = str(token_info.get("url", ""))
        single_use_token = str(token_info.get("token", ""))
        parsed = urllib.parse.urlsplit(url)
        hostname = (parsed.hostname or "").lower()
        # Do not disclose a token to a host that isn't Nitrado-controlled.
        allowed_host = any(hostname == d or hostname.endswith("." + d) for d in ("nitrado.net", "nitra.do"))
        if parsed.scheme != "https" or not allowed_host or not single_use_token:
            raise NitradoError("Unexpected download URL; no request made")
        params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        params.append(("token", single_use_token))
        download_url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(params)))
        request = urllib.request.Request(download_url, headers={"User-Agent":"dayz-console-observatory/0.1"})
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        tmp = destination.with_suffix(destination.suffix + ".part")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response, tmp.open("wb") as stream:
                size = 0
                while True:
                    chunk = response.read(128 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > 50 * 1024 * 1024:
                        raise NitradoError("Log exceeds 50 MiB safety limit")
                    stream.write(chunk)
            tmp.replace(destination)
            return destination
        except urllib.error.HTTPError as exc:
            raise NitradoError(f"Nitrado log download HTTP {exc.code}") from None
        finally:
            if tmp.exists():
                tmp.unlink()
