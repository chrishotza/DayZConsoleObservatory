import tempfile
import unittest
from pathlib import Path

from dayz_observatory.investigate import player_history
from dayz_observatory.store import ingest, get_known_players


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "observatory.db"
        self.log = Path(self.tmp.name) / "sample.ADM"

    def test_sessions_and_history(self):
        self.log.write_text('''AdminLog started on 2026-10-15 at 10:00:00
10:01:00 | Player "A"(id=AAA) is connected
10:02:00 | Player "A" (id=AAA pos=<1, 2, 3>)
10:06:00 | Player "B"(id=BBB) is connected
10:11:00 | Player "A"(id=AAA) has been disconnected
10:12:00 | Player "A"(id=AAA) is connected
10:13:00 | Player "A" (id=AAA pos=<10, 20, 30>)
''')
        ingest(self.db, self.log)
        a = player_history(self.db, "default", "AAA")
        self.assertEqual(len(a["events"]), 5)
        self.assertTrue(all(e["player_id"] == "AAA" for e in a["events"]))
        self.assertEqual(a["latest_observation"]["x"], 10)
        self.assertEqual(a["sessions"][0]["duration_seconds"], 600)
        self.assertEqual(a["sessions"][1]["status"], "no_disconnection_observed")
        self.assertIn("do not prove online", a["disclaimer"])
        self.assertEqual({p["player_id"] for p in get_known_players(self.db)}, {"AAA", "BBB"})

    def test_gaps_and_out_of_order_import(self):
        self.log.write_text('''AdminLog started on 2026-10-15 at 11:00:00
11:30:00 | Player "A"(id=AAA) has been disconnected
''')
        ingest(self.db, self.log)
        earlier = Path(self.tmp.name) / "earlier.ADM"
        earlier.write_text('''AdminLog started on 2026-10-15 at 10:00:00
10:00:00 | Player "A"(id=AAA) is connected
''')
        ingest(self.db, earlier)
        history = player_history(self.db, "default", "AAA")
        self.assertEqual(history["sessions"][0]["status"], "complete")
        self.assertEqual(history["sessions"][0]["duration_seconds"], 5400)
        self.assertEqual(history["events"][0]["kind"], "disconnected")

    def test_disconnection_without_connection(self):
        self.log.write_text('''AdminLog started on 2026-10-15 at 08:00:00
08:01:00 | Player "A"(id=AAA) has been disconnected
''')
        ingest(self.db, self.log)
        self.assertEqual(player_history(self.db, "default", "AAA")["sessions"][0]["status"], "missing_connect")

    def test_unknown_date_never_inferred(self):
        self.log.write_text('12:03:00 | Player "A"(id=AAA) is connected\n')
        ingest(self.db, self.log)
        hist = player_history(self.db, "default", "AAA")
        self.assertIsNone(hist["events"][0]["occurred_at"])
        self.assertEqual(hist["sessions"], [])

    def test_invalid_player_id(self):
        for identifier in ("", "  ", "A\nB", "X" * 257):
            with self.assertRaises(ValueError):
                player_history(self.db, "default", identifier)

    def test_isolates_servers(self):
        self.log.write_text('''AdminLog started on 2026-10-15 at 08:00:00
08:01:00 | Player "A"(id=AAA) is connected
''')
        ingest(self.db, self.log, server="one")
        self.assertEqual(player_history(self.db, "two", "AAA")["events"], [])
        self.assertEqual(get_known_players(self.db, "two"), [])

    def test_empty(self):
        history = player_history(self.db, "default", "missing")
        self.assertEqual(history["latest_observation"], None)
        self.assertEqual(history["sessions"], [])
        self.assertEqual(history["events"], [])


if __name__ == '__main__':
    unittest.main()
