"""Offline SQLite maintenance regressions with private synthetic players only."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from dayz_observatory.maintenance import database_health, backup_database, retain_recent
from dayz_observatory.store import ingest


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.db = self.root / "observatory.sqlite"
        self.adm = self.root / "synthetic.ADM"
        self.adm.write_text(
            'AdminLog started on 2026-10-14 at 12:00:00\n'
            '12:01:00 | Player "SECRET_A" (id=PRIVATE_A pos=<1, 2, 3>)\n'
            '12:02:00 | Player "SECRET_B" (id=PRIVATE_B) is connected\n'
            '12:05:00 | Player "SECRET_B" (id=PRIVATE_B pos=<4, 5, 6>)\n',
            encoding="utf-8")
        ingest(self.db, self.adm, "server-a")
        ingest(self.db, self.adm, "server-b")

    def server_count(self, server):
        with sqlite3.connect(self.db) as db:
            return db.execute("SELECT COUNT(*) FROM events WHERE server=?", (server,)).fetchone()[0]

    def undated_count(self, server):
        with sqlite3.connect(self.db) as db:
            return db.execute(
                "SELECT COUNT(*) FROM events WHERE server=? AND occurred_at IS NULL", (server,)).fetchone()[0]

    def test_health_aggregate_only_no_identifiers(self):
        result = database_health(self.db)
        self.assertEqual(result["events"], 6)
        self.assertEqual(result["servers_with_events"], 2)
        self.assertTrue(result["integrity_ok"])
        self.assertNotIn("PRIVATE_A", str(result))
        self.assertNotIn(str(self.db), str(result))

    def test_missing_db_does_not_create_empty_file(self):
        missing = self.root / "does-not-exist.sqlite"
        with self.assertRaises(ValueError):
            database_health(missing)
        with self.assertRaises(ValueError):
            retain_recent(missing, "server-a", "2026-10-15T00:00:00")
        self.assertFalse(missing.exists())

    def test_backup_is_consistent_with_wal_and_refuses_overwrite(self):
        backup = self.root / "archive" / "snapshot.sqlite"
        result = backup_database(self.db, backup)
        self.assertTrue(result["verified"])
        self.assertEqual(database_health(backup)["events"], 6)
        self.assertIn("private", result["warning"])
        with self.assertRaises(FileExistsError):
            backup_database(self.db, backup)
        self.assertEqual(database_health(backup)["events"], 6)
        if os.name == "posix":
            self.assertEqual(backup.stat().st_mode & 0o777, 0o600)

    def test_backup_failure_cleans_destination(self):
        with self.assertRaises(ValueError):
            backup_database(self.db, self.db)
        with self.assertRaises(ValueError):
            backup_database(self.root / "missing", self.root / "garbage.sqlite")
        self.assertFalse((self.root / "garbage.sqlite").exists())

    def test_preview_never_deletes_or_changes_database(self):
        before = database_health(self.db)
        report = retain_recent(self.db, "server-a", "2026-10-14T12:03:00")
        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual(report["eligible_events"], 2)
        self.assertEqual(report["deleted_events"], 0)
        self.assertEqual(database_health(self.db), before)

    def test_apply_requires_explicit_server_confirmation(self):
        with self.assertRaises(ValueError):
            retain_recent(self.db, "server-a", "2026-10-14T12:03:00", apply=True)
        self.assertEqual(database_health(self.db)["events"], 6)

    def test_apply_is_scoped_preserves_cursors_and_idempotent(self):
        first = retain_recent(self.db, "server-a", "2026-10-14T12:03:00",
                              apply=True, confirm_server="server-a")
        self.assertEqual(first["deleted_events"], 2)
        self.assertEqual(database_health(self.db)["events"], 4)
        self.assertEqual(self.server_count("server-b"), 3)
        self.assertEqual(self.server_count("server-a"), 1)
        self.assertTrue(first["source_cursors_preserved"])
        again = retain_recent(self.db, "server-a", "2026-10-14T12:03:00",
                              apply=True, confirm_server="server-a")
        self.assertEqual(again["deleted_events"], 0)
        self.assertEqual(ingest(self.db, self.adm, "server-a")["new_events"], 0)

    def test_missing_dates_are_preserved(self):
        file = self.root / "undated.ADM"
        file.write_text("12:01:00 | undated event\n")
        ingest(self.db, file, "server-a")
        report = retain_recent(self.db, "server-a", "2026-10-15T00:00:00",
                               apply=True, confirm_server="server-a")
        self.assertEqual(report["undated_preserved"], 1)
        self.assertEqual(self.undated_count("server-a"), 1)

    def test_rejects_bad_cutoff_and_bad_server(self):
        for value in ("2026-10-14", "2026-10-14T12:00:00Z", "2026-02-30T12:00:00",
                      "2026-10-14T2:00:00", "2026-10-14T12:00:00+03:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                retain_recent(self.db, "server-a", value)
        with self.assertRaises(ValueError):
            retain_recent(self.db, "", "2026-10-14T12:03:00")

    def test_symlink_database_and_backup_destination_are_rejected(self):
        alias = self.root / "link.db"
        dest = self.root / "backup-alias.db"
        try:
            alias.symlink_to(self.db)
            dest.symlink_to(self.db)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        with self.assertRaises(ValueError):
            database_health(alias)
        with self.assertRaises(OSError):
            backup_database(self.db, dest)
        self.assertEqual(database_health(self.db)["events"], 6)

    def test_source_integrity_check_does_not_disclose_private_data(self):
        not_db = self.root / "not-db"
        not_db.write_text("this is not sqlite PRIVATE_A")
        with self.assertRaises(ValueError) as err:
            database_health(not_db)
        self.assertNotIn("PRIVATE_A", str(err.exception))


if __name__ == "__main__":
    unittest.main()
