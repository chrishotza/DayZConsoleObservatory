"""Regression tests: volunteer reports must not reveal identifiers."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from dayz_observatory.beta import probe_nitrado, offline_beta_report
from dayz_observatory.cli import main
from dayz_observatory.store import ingest


class FakeNitrado:
    def discover_log_directory(self, service_id):
        return "/games/PRIVATE/noftp/dayzxb/config", {"game": "dayzxb", "username": "PRIVATE"}
    def list_logs(self, service_id, directory):
        return [
            {"name": "SECRET.ADM", "path": directory + "/SECRET.ADM", "size": 20, "modified_at": "2026-10-15"},
            {"name": "PERSONAL.RPT", "path": directory + "/PERSONAL.RPT"},
        ]


class BetaSafetyTests(unittest.TestCase):
    def test_probe_suppresses_identifying_metadata(self):
        output = probe_nitrado(FakeNitrado(), 12345678)
        self.assertEqual(output["adm_files_visible"], 1)
        self.assertEqual(output["rpt_files_visible"], 1)
        self.assertEqual(output["adm_metadata_cache_eligible"], 1)
        self.assertFalse(output["download_tested"])
        dump = json.dumps(output)
        for value in ("12345678", "PRIVATE", "SECRET", "PERSONAL", "/games/", "2026-10-15"):
            self.assertNotIn(value, dump)

    def test_offline_summary_contains_only_aggregates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log = root / "PRIVATE.ADM"
            log.write_text("AdminLog started on 2026-10-15 at 12:00:00\n"
                '12:01:00 | Player "SECRET" (id=PRIVATE_ID pos=<123, 456, 7>)\n')
            ingest(root / "db.sqlite", log, "PRIVATE_SERVER")
            result = offline_beta_report(root / "db.sqlite", "PRIVATE_SERVER")
            self.assertEqual(result["position_observations"], 1)
            dump = json.dumps(result)
            for value in ("SECRET", "PRIVATE_ID", "PRIVATE_SERVER", "2026-10-15", "PRIVATE.ADM"):
                self.assertNotIn(value, dump)

    def test_cli_probe_safe_output(self):
        with patch("dayz_observatory.cli.NitradoClient", return_value=FakeNitrado()):
            out = io.StringIO()
            with redirect_stdout(out):
                main(["nitrado", "12345678", "--probe"])
        data = json.loads(out.getvalue())
        self.assertTrue(data["xbox_service_detected"])
        self.assertNotIn("12345678", out.getvalue())

    def test_modes_are_mutually_exclusive(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["nitrado", "123", "--probe", "--list-only"])
        self.assertEqual(error.exception.code, 2)

    def test_probe_has_no_download_or_player_data(self):
        result = probe_nitrado(FakeNitrado(), 42)
        self.assertFalse(result["download_tested"])
        self.assertFalse(result["player_data_accessed"])


if __name__ == "__main__":
    unittest.main()
