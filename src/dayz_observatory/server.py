"""Loopback-only browser UI; optional local ADM import, never game modification.

Browser POSTs require same-origin and a custom header to reject cross-site
requests aimed at a service on localhost. No public network binding or CORS.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import tempfile
from threading import Lock
from urllib.parse import parse_qs, urlsplit

from .store import ingest, get_events, get_players, get_known_players, get_quality_report
from .investigate import player_history
from .incidents import search_incidents

WEB = Path(__file__).parent / "web"
MAX_ADM_BYTES = 8 * 1024 * 1024
DEMO_SERVER = "__dayz_synthetic_demo__"
DEMO_ADM = (
    'AdminLog started on 2026-10-15 at 14:00:00\n'
    '14:00:20 | Player "SYNTHETIC_RAVEN" (id=SYNTH_RAVEN) is connected\n'
    '14:01:00 | Player "SYNTHETIC_RAVEN" (id=SYNTH_RAVEN pos=<3450, 7810, 110>)\n'
    '14:02:30 | Player "SYNTHETIC_FOX" (id=SYNTH_FOX pos=<3610, 7890, 105>)\n'
    '14:05:00 | Player "SYNTHETIC_RAVEN" (id=SYNTH_RAVEN pos=<3700, 8000, 109>)\n'
    '14:07:30 | Player "SYNTHETIC_FOX" (id=SYNTH_FOX pos=<3850, 8110, 107>)\n'
    '14:08:00 | Player "SYNTHETIC_RAVEN" (id=SYNTH_RAVEN) has been disconnected\n'
).encode("utf-8")


def _local_import(db_path: str, server: str, name: str, payload: bytes) -> dict:
    if (not isinstance(name, str) or not 1 <= len(name) <= 128
            or name in (".", "..") or "/" in name or "\\" in name
            or any(ord(c) < 32 for c in name) or not name.lower().endswith(".adm")):
        raise ValueError("Select a valid .ADM file")
    if not payload or len(payload) > MAX_ADM_BYTES:
        raise ValueError("ADM must contain between 1 byte and 8 MiB")
    # Never use a user-supplied filename or server ID as a disk path.
    folder = Path(db_path).expanduser().resolve().parent / "private-imports"
    folder.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256((server + "\0" + name).encode("utf-8")).hexdigest()
    target = folder / (digest + ".ADM")
    if target.is_symlink():
        raise ValueError("Refusing symlink destination")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=folder, prefix=".upload-",
                                         suffix=".part", delete=False) as out:
            temporary = out.name
            if os.name == "posix":
                os.fchmod(out.fileno(), 0o600)
            out.write(payload)
        os.replace(temporary, target)
        temporary = None
        result = ingest(db_path, target, server)
        return {"new_events": result["new_events"],
                "read_events": result["read_events"],
                "historical_only": True}
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def make_server(db_path: str, server: str = "default", port: int = 8765) -> ThreadingHTTPServer:
    """Build an explicitly localhost-only HTTP server (port 0 for tests)."""
    import_lock = Lock()

    class Handler(BaseHTTPRequestHandler):
        def _scope(self, query: dict) -> str:
            return DEMO_SERVER if query.get("scope", ["local"])[0] == "demo" else server

        def do_GET(self):
            request = urlsplit(self.path)
            if request.path in ("/api/events", "/api/players", "/api/investigate",
                                "/api/known-players", "/api/quality", "/api/incidents"):
                query = parse_qs(request.query)
                selected = self._scope(query)
                try:
                    if request.path.endswith("/quality"):
                        payload = get_quality_report(db_path, selected)
                    elif request.path.endswith("/incidents"):
                        payload = search_incidents(db_path, selected,
                            query.get("start", [""])[0], query.get("end", [""])[0],
                            gap_seconds=int(query.get("gap_seconds", ["300"])[0]),
                            max_records=int(query.get("max_records", ["500"])[0]),
                            player_id=query.get("player_id", [None])[0],
                            private=query.get("details", ["0"])[0] == "1")
                    elif request.path.endswith("/events"):
                        limit = int(query.get("limit", ["300"])[0])
                        payload = get_events(db_path, selected, query.get("kind", [None])[0], limit)
                    elif request.path.endswith("/known-players"):
                        payload = get_known_players(db_path, selected)
                    elif request.path.endswith("/investigate"):
                        payload = player_history(db_path, selected,
                            query.get("player_id", [""])[0], int(query.get("limit", ["300"])[0]))
                    else:
                        payload = get_players(db_path, selected)
                except (ValueError, OverflowError):
                    self.send_error(400, "Invalid query")
                    return
                self.reply(json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")
                return
            filename = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}.get(request.path)
            if not filename:
                self.send_error(404)
                return
            path = WEB / filename
            content_type = ("text/html" if filename.endswith("html") else
                            "application/javascript" if filename.endswith("js") else "text/css")
            self.reply(path.read_bytes(), content_type + "; charset=utf-8")

        def do_POST(self):
            request = urlsplit(self.path)
            if request.path not in ("/api/import", "/api/demo"):
                self.send_error(404)
                return
            # DNS-rebinding/CSRF barrier: reject foreign Origin, host and
            # browser simple-form POSTs. JS fetch sends this custom header.
            expected = f"http://127.0.0.1:{self.server.server_port}"
            if (self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}"
                    or self.headers.get("Origin") != expected
                    or self.headers.get("X-DayZ-Local-UI") != "v1"):
                self.send_error(403, "Local browser request required")
                return
            if request.path == "/api/import":
                if self.headers.get("Content-Type") != "application/octet-stream":
                    self.send_error(415, "ADM binary upload required")
                    return
                try:
                    length = int(self.headers.get("Content-Length", ""))
                except ValueError:
                    self.send_error(411, "Content length required")
                    return
                if length <= 0 or length > MAX_ADM_BYTES:
                    self.send_error(413, "ADM exceeds 8 MiB or is empty")
                    return
                name = parse_qs(request.query).get("name", [""])[0]
                data = self.rfile.read(length)
                if len(data) != length:
                    self.send_error(400, "Incomplete upload")
                    return
                try:
                    with import_lock:
                        report = _local_import(db_path, server, name, data)
                except ValueError:
                    self.send_error(400, "Invalid ADM file")
                    return
                except OSError:
                    self.send_error(500, "Local import failed")
                    return
            else:
                if self.headers.get("Content-Length", "0") not in ("", "0"):
                    self.send_error(400, "Demo request must be empty")
                    return
                with import_lock:
                    report = _local_import(db_path, DEMO_SERVER, "SYNTHETIC_DEMO.ADM", DEMO_ADM)
                report["synthetic_only"] = True
            self.reply(json.dumps(report).encode("utf-8"), "application/json; charset=utf-8")

        def reply(self, data: bytes, content_type: str):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                "default-src 'self'; style-src 'self'; script-src 'self'; "
                "connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):
            return  # Never log sensitive query values.

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(db_path: str, server: str = "default", port: int = 8765) -> None:
    http = make_server(db_path, server, port)
    print(f"DayZ Console Observatory (local only): http://127.0.0.1:{http.server_port}")
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http.server_close()
