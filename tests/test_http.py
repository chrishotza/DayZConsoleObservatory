"""Real loopback HTTP tests, never internet and never a DayZ client."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
import urllib.error
import urllib.request

from dayz_observatory.server import make_server
from dayz_observatory.store import ingest


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name)/'local.db'
        log = Path(self.tmp.name)/'sample.ADM'
        log.write_text('AdminLog started on 2026-10-15 at 12:00:00\n'
                       '12:01:00 | Player "Demo" (id=ABC pos=<12, 34, 56>)\n')
        ingest(self.db, log)
        self.host = make_server(str(self.db), port=0)
        self.addCleanup(self.host.server_close)
        self.thread = threading.Thread(target=self.host.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_host)
        self.base = f'http://127.0.0.1:{self.host.server_port}'

    def stop_host(self):
        self.host.shutdown()
        self.thread.join(timeout=3)

    def get(self, route):
        return urllib.request.urlopen(self.base+route, timeout=3)

    def test_quality_is_real_json_and_private(self):
        with self.get('/api/quality') as response:
            self.assertEqual(response.status,200)
            self.assertIn('application/json',response.headers['Content-Type'])
            self.assertEqual(response.headers['Cache-Control'],'no-store')
            self.assertIn("'self'",response.headers['Content-Security-Policy'])
            quality=json.load(response)
        self.assertEqual(quality['events'],1)
        self.assertEqual(quality['position_observations'],1)
        self.assertEqual(quality['imported_sources'],1)
        self.assertEqual(self.host.server_address[0],'127.0.0.1')

    def test_history_and_players_are_isolated_and_read_only(self):
        with self.get('/api/investigate?player_id=ABC') as response:
            history=json.load(response)
        self.assertEqual(history['latest_observation']['x'],12)
        self.assertEqual(history['player_id'],'ABC')
        with self.get('/api/known-players') as response:
            self.assertEqual(json.load(response)[0]['player_id'],'ABC')

    def test_bad_player_query_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('/api/investigate?player_id=')
        self.assertEqual(error.exception.code,400)

    def test_incidents_api_defaults_to_aggregate_only(self):
        url = ('/api/incidents?start=2026-10-15T12%3A00%3A00'
               '&end=2026-10-15T12%3A30%3A00')
        with self.get(url) as response:
            result = json.load(response)
        self.assertEqual(result['group_count'], 1)
        self.assertEqual(result['scanned_records'], 1)
        self.assertNotIn('ABC', json.dumps(result))
        self.assertNotIn('Demo', json.dumps(result))

    def test_incidents_api_private_details_are_loopback_only(self):
        url = ('/api/incidents?start=2026-10-15T12%3A00%3A00'
               '&end=2026-10-15T12%3A30%3A00&details=1')
        with self.get(url) as response:
            result = json.load(response)
        self.assertEqual(result['groups'][0]['records'][0]['player_id'], 'ABC')
        self.assertEqual(self.host.server_address[0], '127.0.0.1')

    def test_incidents_api_invalid_window_returns_400(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('/api/incidents?start=invalid&end=2026-10-15T12%3A30%3A00')
        self.assertEqual(error.exception.code, 400)

    def test_unrecognized_path_is_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('/api/private-logs')
        self.assertEqual(error.exception.code,404)

    def test_ui_served_with_security_headers(self):
        with self.get('/') as response:
            data=response.read().decode('utf-8')
            self.assertIn('Evidence quality',data)
            self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')


if __name__ == '__main__':
    unittest.main()
