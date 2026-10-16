"""Regression: Windows file IDs can exceed SQLite signed INTEGER bounds."""
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sqlite3
import tempfile
import unittest

from dayz_observatory.store import _sqlite_file_id, ingest


class PlatformFileIdentityTests(unittest.TestCase):
    def test_normal_posix_file_ids_remain_identical(self):
        for value in (0, 1, 43210, (1 << 63) - 1, -(1 << 63)):
            self.assertEqual(_sqlite_file_id(value), value)

    def test_oversized_windows_ids_are_stable_and_sqlite_safe(self):
        for huge in (1 << 63, 1 << 99, (1 << 128) - 1, -(1 << 100)):
            value = _sqlite_file_id(huge)
            self.assertGreater(value, 0)
            self.assertLess(value, (1 << 63))
            self.assertEqual(value, _sqlite_file_id(huge))
            with tempfile.TemporaryDirectory() as tmp:
                with closing(sqlite3.connect(Path(tmp) / "ids.sqlite")) as db:
                    db.execute("CREATE TABLE identity (value INTEGER)")
                    db.execute("INSERT INTO identity VALUES (?)", (value,))
                    self.assertEqual(db.execute("SELECT value FROM identity").fetchone()[0], value)

    def test_ingest_oversized_inode_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = (root / "test.ADM").resolve()
            db = root / "events.sqlite"
            file.write_text(
                'AdminLog started on 2026-10-15 at 12:00:00\n'
                '12:01:00 | Player "SYNTH" (id=SYNTH_ID pos=<1, 2, 3>)\n',
                encoding="utf-8",
            )
            regular = Path.stat
            huge_inode, huge_device = (1 << 114) + 17, (1 << 97) + 9
            def oversized_ids(path, *args, **kwargs):
                st = regular(path, *args, **kwargs)
                if str(path) == str(file):
                    return SimpleNamespace(st_ino=huge_inode, st_dev=huge_device, st_size=st.st_size)
                return st
            with patch.object(Path, "stat", oversized_ids):
                first = ingest(db, file)
                second = ingest(db, file)
            self.assertEqual(first["new_events"], 1)
            self.assertEqual(second["new_events"], 0)
            self.assertFalse(second["rotated"])
            with closing(sqlite3.connect(db)) as conn:
                identity = conn.execute("SELECT device,inode FROM sources").fetchone()
                self.assertEqual(identity, (_sqlite_file_id(huge_device), _sqlite_file_id(huge_inode)))


if __name__ == "__main__":
    unittest.main()
