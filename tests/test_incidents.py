"""End-to-end incident clustering on synthetic server-local ADM logs."""
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from dayz_observatory.incidents import search_incidents
from dayz_observatory.store import ingest
from dayz_observatory.cli import main


class IncidentTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.db = self.root / "cases.sqlite"
        self.adm = self.root / "PRIVATE.ADM"
        self.adm.write_text(
            "AdminLog started on 2026-10-15 at 12:00:00\n"
            '12:00:10 | Player "Alice" (id=SECRET_A) is connected\n'
            '12:01:30 | Player "Bob" (id=SECRET_B pos=<120, 340, 5>)\n'
            '12:02:00 | Some combat hit event\n'
            '12:12:00 | Player "Alice" (id=SECRET_A pos=<140, 350, 5>)\n'
            '12:13:00 | Player "Alice" (id=SECRET_A) has been disconnected\n'
            '12:25:00 | Player "Bob" (id=SECRET_B pos=<200, 400, 5>)\n',
            encoding="utf-8")
        ingest(self.db, self.adm, "PRIVATE_SERVER")

    def search(self, **kwargs):
        return search_incidents(self.db, "PRIVATE_SERVER",
                                "2026-10-15T12:00:00", "2026-10-15T12:30:00", **kwargs)

    def test_clusters_are_chronological_and_distinct(self):
        result = self.search(gap_seconds=120)
        self.assertEqual(result["group_count"], 3)
        self.assertEqual([g["record_count"] for g in result["groups"]], [3, 2, 1])
        self.assertEqual(result["scanned_records"], 6)
        self.assertFalse(result["truncated"])

    def test_player_filter_keeps_other_players_in_related_group(self):
        result = self.search(gap_seconds=120, player_id="SECRET_A", private=True)
        self.assertEqual(result["group_count"], 2)
        self.assertEqual([g["record_count"] for g in result["groups"]], [3, 2])
        self.assertEqual(result["groups"][0]["known_players"], 2)

    def test_unmatched_player_does_not_invent_incidents(self):
        result = self.search(player_id="MISSING_ID")
        self.assertEqual(result["groups"], [])
        self.assertEqual(result["selected_records"], 0)

    def test_summary_never_leaks_identifiers_location_time_or_path(self):
        result = self.search(player_id="SECRET_A")
        encoded = json.dumps(result)
        for secret in ("SECRET_A", "SECRET_B", "Alice", "Bob", "PRIVATE_SERVER",
                       "PRIVATE.ADM", "2026-10-15", "340", "12:01:30", "combat hit event"):
            self.assertNotIn(secret, encoded)
        self.assertEqual(result["disclosure"], "aggregate-only")

    def test_private_mode_preserves_source_provenance(self):
        result = self.search(gap_seconds=120, private=True)
        record = result["groups"][0]["records"][0]
        self.assertEqual(record["player_id"], "SECRET_A")
        self.assertIn("byte_offset", record)
        self.assertEqual(len(record["record_fingerprint_sha256"]), 64)
        self.assertEqual(result["query"]["server"], "PRIVATE_SERVER")

    def test_exact_boundaries_and_undated_excluded(self):
        single = search_incidents(self.db, "PRIVATE_SERVER", "2026-10-15T12:01:30",
                                  "2026-10-15T12:01:30")
        self.assertEqual(single["selected_records"], 1)
        self.assertTrue(single["undated_events_excluded"])

    def test_limit_has_explicit_truncation_warning(self):
        result = self.search(max_records=2)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["scanned_records"], 2)
        self.assertEqual(result["group_count"], 1)

    def test_time_window_never_crosses_servers(self):
        ingest(self.db, self.adm, "OTHER_PRIVATE_SERVER")
        self.assertEqual(self.search()["scanned_records"], 6)
        self.assertEqual(search_incidents(self.db, "NO_DATA", "2026-10-15T12:00:00",
                                          "2026-10-15T12:30:00")["scanned_records"], 0)

    def test_reject_invalid_window(self):
        for begin, end in [
            ("2026-10-15T12:00", "2026-10-15T12:30:00"),
            ("2026-02-29T00:00:00", "2026-03-01T00:00:00"),
            ("2026-10-15T12:00:00Z", "2026-10-15T12:30:00"),
            ("2026-10-15T12:31:00", "2026-10-15T12:30:00"),
            ("2026-10-15T00:00:00", "2026-10-18T00:00:00"),
        ]:
            with self.subTest(begin=begin), self.assertRaises(ValueError):
                search_incidents(self.db, "PRIVATE_SERVER", begin, end)

    def test_reject_bad_limits(self):
        for name, value in [("gap_seconds", -1), ("gap_seconds", 3601),
                            ("gap_seconds", True), ("max_records", 0),
                            ("max_records", 2001), ("max_records", True),
                            ("player_id", "\x00")]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.search(**{name: value})

    def test_cli_creates_anonymous_file_and_never_prints_identity(self):
        dest = self.root / "summary.json"
        out = StringIO()
        with redirect_stdout(out):
            main(["incidents", "2026-10-15T12:00:00", "2026-10-15T12:30:00",
                  "--server", "PRIVATE_SERVER", "--db", str(self.db),
                  "--player-id", "SECRET_A", "--out", str(dest)])
        data = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(data["disclosure"], "aggregate-only")
        self.assertEqual(data["group_count"], 2)
        self.assertNotIn("SECRET_A", dest.read_text() + out.getvalue())

    def test_cli_private_mode_is_explicit(self):
        dest = self.root / "private.json"
        with redirect_stdout(StringIO()):
            main(["incidents", "2026-10-15T12:00:00", "2026-10-15T12:30:00",
                  "--server", "PRIVATE_SERVER", "--db", str(self.db),
                  "--private", "--out", str(dest)])
        self.assertEqual(json.loads(dest.read_text())["disclosure"], "private")


if __name__ == "__main__":
    unittest.main()
