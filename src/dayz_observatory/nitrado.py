"""Read-only Nitrado Xbox service adapter with strict transport boundaries.

Only read endpoints are implemented. No redirects are followed (including those
from a signed download URL), to avoid leaking either the account bearer token or
a short-lived download token to third-party hosts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import posixpath
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.nitrado.net"
MAX_API_BYTES = 2 * 1024 * 1024
MAX_LOG_BYTES = 50 * 1024 * 1024
ALLOWED_DOWNLOAD_HOSTS = ("nitrado.net", "nitra.do")


class NitradoError(RuntimeError):
    """Safe, non-secret exception for read-only Nitrado operations."""


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib's default redirect handler can forward authentication headers.
        return None


class NitradoClient:
    def __init__(self, token: str | None = None, timeout: int = 30):
        self.token = token if token is not None else os.environ.get("NITRADO_TOKEN")
        if not self.token or not self.token.strip():
            raise NitradoError("Set NITRADO_TOKEN in your environment. Never put it in source files.")
        if any(ord(c) < 33 or ord(c) > 126 for c in self.token):
            raise NitradoError("Invalid token format")
        if not 1 <= timeout <= 120:
            raise ValueError("timeout must be between 1 and 120 seconds")
        self.timeout = timeout
        self._opener = urllib.request.build_opener(_RejectRedirects())

    def _open(self, request: urllib.request.Request):
        return self._opener.open(request, timeout=self.timeout)

    @staticmethod
    def _service_id(service_id: int) -> int:
        value = int(service_id)
        if value <= 0:
            raise ValueError("service_id must be positive")
        return value

    def _json(self, path: str, params: dict | None = None) -> dict:
        url = BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
            "User-Agent": "dayz-console-observatory/0.4",
        })
        for attempt in range(2):
            try:
                with self._open(request) as response:
                    payload = response.read(MAX_API_BYTES + 1)
                    if len(payload) > MAX_API_BYTES:
                        raise NitradoError("Nitrado API response exceeds the 2 MiB safety limit")
                    data = json.loads(payload)
                    if not isinstance(data, dict):
                        raise NitradoError("Unexpected API response shape")
                    return data
            except urllib.error.HTTPError as exc:
                # urllib.error.HTTPError owns a response stream that MUST be
                # closed, even when we retry. Otherwise Python 3.14 can emit
                # an unraisable ResourceWarning on garbage collection.
                status = exc.code
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                exc.close()
                if status in (429, 503) and attempt == 0:
                    try:
                        delay = max(1, int(retry_after)) if retry_after else 1
                    except (TypeError, ValueError):
                        delay = 1
                    if delay <= 5:
                        time.sleep(delay)
                        continue
                raise NitradoError(f"Nitrado API HTTP {status} while reading {path}") from None
            except (urllib.error.URLError, OSError, ValueError) as exc:
                raise NitradoError(f"Nitrado API unavailable: {exc.__class__.__name__}") from None
        raise NitradoError("Nitrado API request retries exhausted")

    def gameserver(self, service_id: int) -> dict:
        data = self._json(f"/services/{self._service_id(service_id)}/gameservers")
        server = data.get("data", {}).get("gameserver")
        if not isinstance(server, dict):
            raise NitradoError("Unexpected gameserver response shape")
        return server

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
        data = self._json(f"/services/{self._service_id(service_id)}/gameservers/file_server/list", {"dir": directory})
        entries = data.get("data", {}).get("entries", [])
        if not isinstance(entries, list):
            raise NitradoError("Unexpected file list response shape")
        result = []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("type") != "file":
                continue
            name = entry.get("name")
            remote = entry.get("path")
            if (isinstance(name, str) and isinstance(remote, str)
                    and name.lower().endswith((".adm", ".rpt"))
                    and name not in (".", "..") and "/" not in name and "\\" not in name
                    and remote == directory.rstrip("/") + "/" + name):
                result.append(entry)
        return result

    @staticmethod
    def _validate_download_url(url: str) -> str:
        try:
            parsed = urllib.parse.urlsplit(url)
            hostname = (parsed.hostname or "").lower()
            if (parsed.scheme != "https" or not hostname
                    or parsed.username is not None or parsed.password is not None
                    or parsed.port not in (None, 443) or parsed.fragment):
                raise ValueError("Invalid URL components")
        except ValueError:
            raise NitradoError("Unexpected download URL; no request made") from None
        if not any(hostname == domain or hostname.endswith("." + domain) for domain in ALLOWED_DOWNLOAD_HOSTS):
            raise NitradoError("Unexpected download host; no request made")
        return url

    def download_log(self, service_id: int, remote_path: str, destination: str | Path, allowed_directory: str) -> Path:
        root = allowed_directory.rstrip("/")
        # Reject traversal *before* sending the remote path to the service.
        if (not root.startswith("/games/") or not remote_path.startswith(root + "/")
                or posixpath.normpath(remote_path) != remote_path
                or posixpath.dirname(remote_path) != root
                or not remote_path.lower().endswith((".adm", ".rpt"))
                or "\\" in remote_path):
            raise NitradoError("Refusing unsafe or non-log remote file")
        response = self._json(f"/services/{self._service_id(service_id)}/gameservers/file_server/download", {"file": remote_path})
        token_info = response.get("data", {}).get("token", {})
        if not isinstance(token_info, dict):
            raise NitradoError("Unexpected download token response")
        url = self._validate_download_url(str(token_info.get("url", "")))
        single_use_token = token_info.get("token")
        if not isinstance(single_use_token, str) or not single_use_token:
            raise NitradoError("Missing download token")
        parsed = urllib.parse.urlsplit(url)
        # Fail closed if the API ever starts returning an already-signed URL.
        params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if any(k.lower() == "token" for k, _ in params):
            raise NitradoError("Unexpected pre-signed download URL")
        params.append(("token", single_use_token))
        download_url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(params)))
        request = urllib.request.Request(download_url, headers={"User-Agent": "dayz-console-observatory/0.3"})
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        name: str | None = None
        try:
            # Same directory guarantees os.replace is atomic on a single filesystem.
            with tempfile.NamedTemporaryFile(mode="wb", prefix=".dayz-log-", suffix=".part",
                                             dir=destination.parent, delete=False) as stream:
                name = stream.name
                with self._open(request) as http:
                    size = 0
                    while True:
                        chunk = http.read(128 * 1024)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_LOG_BYTES:
                            raise NitradoError("Log exceeds 50 MiB safety limit")
                        stream.write(chunk)
            os.replace(name, destination)
            return destination
        except urllib.error.HTTPError as exc:
            status = exc.code
            exc.close()
            raise NitradoError(f"Nitrado log download HTTP {status}") from None
        except (urllib.error.URLError, OSError) as exc:
            raise NitradoError(f"Nitrado log download unavailable: {exc.__class__.__name__}") from None
        finally:
            if name is not None:
                try:
                    Path(name).unlink(missing_ok=True)
                except OSError:
                    pass
