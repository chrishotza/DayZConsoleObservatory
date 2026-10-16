"""Argparse and privacy checks for owner-only database maintenance commands."""
import io
import json
from contextlib import redirect_stdout, redirect_stderr
import tempfile
import unittest
from pathlib import Path

from dayz_observatory.store import ingest
from dayz_observatory.cli import main


class MaintenanceCLITests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.db = self.root / "data.sqlite"
        log = self.root / "PRIVATE.ADM"
        log.write_text(
            'AdminLog started on 2026-10-15 at 12:00:00\n'
            '12:01:00 | Player "PRIVATE_PLAYER" (id=SECRET_UID pos=<13, 17, 2>)\n')
        ingest(self.db, log, "SECRET_SERVICE")

    def capture(self, argv):
        out = io.StringIO()
        with redirect_stdout(out):
            main(argv)
        return json.loads(out.getvalue())

    def test_doctor_cli_avoids_sensitive_details(self):
        result = self.capture(["doctor", "--db", str(self.db)])
        self.assertEqual(result["result"], "ok")
        self.assertNotIn("SECRET_UID", json.dumps(result))
        self.assertNotIn(str(self.db), json.dumps(result))

    def test_backup_cli_creates_protected_copy(self):
        path = self.root / "snapshot.sqlite"
        report = self.capture(["backup", "--db", str(self.db), "--out", str(path)])
        self.assertTrue(report["verified"])
        self.assertTrue(path.exists())
        self.assertNotIn("PRIVATE_PLAYER", json.dumps(report))

    def test_retention_preview_and_apply_are_separate(self):
        preview = self.capture(["retain", "--db", str(self.db), "--server", "SECRET_SERVICE",
                                "--before", "2026-10-16T00:00:00"])
        self.assertEqual(preview["eligible_events"], 1)
        self.assertEqual(preview["deleted_events"], 0)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.capture(["retain", "--db", str(self.db), "--server", "SECRET_SERVICE",
                          "--before", "2026-10-16T00:00:00", "--apply"])
        done = self.capture(["retain", "--db", str(self.db), "--server", "SECRET_SERVICE",
                             "--before", "2026-10-16T00:00:00", "--apply",
                             "--confirm-server", "SECRET_SERVICE"])
        self.assertEqual(done["deleted_events"], 1)
        self.assertNotIn("SECRET_SERVICE", json.dumps(done))


if __name__ == "__main__":
    unittest.main()
