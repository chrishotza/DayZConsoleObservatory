"""Read-only local dashboard, bound to loopback by design."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from .store import get_events, get_players, get_known_players, get_quality_report
from .investigate import player_history

WEB = Path(__file__).parent / "web"


def make_server(db_path: str, server: str = "default", port: int = 8765) -> ThreadingHTTPServer:
    """Create loopback-only server. Port 0 is supported for isolated offline tests."""
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            request = urlsplit(self.path)
            if request.path in ("/api/events", "/api/players", "/api/investigate", "/api/known-players", "/api/quality"):
                query = parse_qs(request.query)
                try:
                    if request.path.endswith("/quality"):
                        payload = get_quality_report(db_path, server)
                    elif request.path.endswith("/events"):
                        limit = int(query.get("limit", ["300"])[0]); kind = query.get("kind", [None])[0]
                        payload = get_events(db_path, server, kind, limit)
                    elif request.path.endswith("/known-players"):
                        payload = get_known_players(db_path, server)
                    elif request.path.endswith("/investigate"):
                        player_id = query.get("player_id", [""])[0]
                        limit = int(query.get("limit", ["300"])[0])
                        payload = player_history(db_path, server, player_id, limit)
                    else:
                        payload = get_players(db_path, server)
                except (ValueError, OverflowError):
                    self.send_error(400, "Invalid query"); return
                self.reply(json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")
                return
            filename = {"/":"index.html", "/app.js":"app.js", "/style.css":"style.css"}.get(request.path)
            if not filename:
                self.send_error(404); return
            path = WEB / filename
            content_type = "text/html" if filename.endswith("html") else "application/javascript" if filename.endswith("js") else "text/css"
            self.reply(path.read_bytes(), content_type + "; charset=utf-8")

        def reply(self, data, content_type):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):
            return  # no names/IDs in HTTP access logs

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def serve(db_path: str, server: str = "default", port: int = 8765) -> None:
    server_http = make_server(db_path, server, port)
    print(f"DayZ Console Observatory (local only): http://127.0.0.1:{server_http.server_port}")
    try:
        server_http.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server_http.server_close()
