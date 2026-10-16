"""Browser workflow tests: true HTTP POST, no internet or DayZ installation."""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from dayz_observatory.server import make_server, MAX_ADM_BYTES
from dayz_observatory.store import get_quality_report


class BrowserImportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = self.root / "events.sqlite"
        self.http = make_server(str(self.db), server="live_owner", port=0)
        self.url = f"http://127.0.0.1:{self.http.server_port}"
        self.worker = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.http.shutdown()
        self.worker.join(timeout=4)
        self.http.server_close()

    def post(self, path, data=b"", *, origin=True, local_header=True, host=None, content_type=None):
        headers = {}
        if origin:
            headers["Origin"] = self.url
        if local_header:
            headers["X-DayZ-Local-UI"] = "v1"
        if content_type:
            headers["Content-Type"] = content_type
        if host:
            headers["Host"] = host
        return urllib.request.urlopen(
            urllib.request.Request(self.url + path, data=data, headers=headers, method="POST"), timeout=3)

    def get(self, path):
        with urllib.request.urlopen(self.url + path, timeout=3) as response:
            return json.load(response)

    def test_import_adm_without_cli_and_detect_append(self):
        name = urllib.parse.quote("owner.ADM")
        one = (b"AdminLog started on 2026-10-15 at 12:00:00\n"
               b'12:01:00 | Player "LOCAL" (id=ONE pos=<1, 2, 3>)\n')
        path = "/api/import?name=" + name
        with self.post(path, one, content_type="application/octet-stream") as response:
            self.assertEqual(json.load(response)["new_events"], 1)
        with self.post(path, one, content_type="application/octet-stream") as response:
            self.assertEqual(json.load(response)["new_events"], 0)
        with self.post(path, one + b"12:06:00 | second event\n",
                       content_type="application/octet-stream") as response:
            self.assertEqual(json.load(response)["new_events"], 1)
        self.assertEqual(self.get("/api/quality")["events"], 2)

    def test_demo_is_isolated_from_owner_records_and_idempotent(self):
        with self.post("/api/demo") as response:
            report = json.load(response)
        self.assertTrue(report["synthetic_only"])
        self.assertEqual(self.get("/api/quality")["events"], 0)
        first = self.get("/api/quality?scope=demo")
        self.assertGreater(first["events"], 3)
        self.assertEqual(self.get("/api/known-players"), [])
        with self.post("/api/demo") as response:
            self.assertEqual(json.load(response)["new_events"], 0)
        self.assertEqual(self.get("/api/quality?scope=demo")["events"], first["events"])

    def test_origin_custom_header_and_host_required(self):
        for kwargs in ({"origin": False}, {"local_header": False},
                       {"host": "evil.example"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(urllib.error.HTTPError) as ctx:
                self.post("/api/demo", **kwargs)
            self.assertEqual(ctx.exception.code, 403)
        self.assertFalse(self.db.exists())

    def test_rejects_path_traversal_and_non_adm(self):
        for name in ("../../file.ADM", "x.RPT", "dir\\x.ADM", ""):
            with self.subTest(name=name), self.assertRaises(urllib.error.HTTPError) as ctx:
                self.post("/api/import?name=" + urllib.parse.quote(name), b"data\n",
                          content_type="application/octet-stream")
            self.assertEqual(ctx.exception.code, 400)

    def test_rejects_large_and_wrong_media(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.post("/api/import?name=x.ADM", b"x", content_type="text/plain")
        self.assertEqual(ctx.exception.code, 415)
        # Send only headers claiming an oversized body. The server must return
        # HTTP 413 before reading bytes. Sending 8+ MiB then receiving an early
        # rejection causes BrokenPipe/WinError 10053 on some operating systems.
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", self.http.server_port, timeout=3)
        try:
            conn.putrequest("POST", "/api/import?name=x.ADM")
            conn.putheader("Origin", self.url)
            conn.putheader("X-DayZ-Local-UI", "v1")
            conn.putheader("Content-Type", "application/octet-stream")
            conn.putheader("Content-Length", str(MAX_ADM_BYTES + 1))
            conn.endheaders()
            response = conn.getresponse()
            self.assertEqual(response.status, 413)
            response.read()
        finally:
            conn.close()

    def test_import_does_not_expose_raw_log_in_response(self):
        content = ('AdminLog started on 2026-10-15 at 12:00:00\n'
                   '12:03:00 | Player "PERSONAL_NAME" (id=PRIVATE_ID pos=<30, 40, 5>)\n')
        with self.post("/api/import?name=private.ADM", content.encode(),
                       content_type="application/octet-stream") as response:
            dumped = response.read().decode("utf-8")
        self.assertNotIn("PERSONAL_NAME", dumped)
        self.assertNotIn("PRIVATE_ID", dumped)
        self.assertNotIn("private.ADM", dumped)
        self.assertNotIn(str(self.root), dumped)

    def test_private_get_api_rejects_dns_rebinding_host(self):
        request = urllib.request.Request(
            self.url + "/api/players", headers={"Host": "remote.example"})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(request, timeout=3)
        self.assertEqual(ctx.exception.code, 403)

    def test_browser_onboarding_controls_exist(self):
        with urllib.request.urlopen(self.url, timeout=3) as response:
            page = response.read().decode("utf-8")
        for control in ("modeSelect", "admFile", "importButton", "demoButton",
                        "incidentStart", "incidentEnd", "incidentSearch"):
            with self.subTest(control=control):
                self.assertIn('id="' + control + '"', page)
        self.assertIn("SYNTHETIC", page)
        self.assertNotIn("NITRADO_TOKEN", page)

    def test_unknown_route_is_not_a_write_operation(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.post("/api/settings", b"{}", content_type="application/octet-stream")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
