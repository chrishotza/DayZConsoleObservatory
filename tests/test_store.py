import tempfile
import unittest
from pathlib import Path
from dayz_observatory.store import ingest,get_events,get_players

class IngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'db.sqlite'
        self.log=Path(self.tmp.name)/'test.ADM'
    def test_deduplication(self):
        self.log.write_text('AdminLog started on 2026-10-14 at 12:00:00\n12:01:00 | Player "SYNTH" (id=SYNTHID pos=<1, 2, 3>)\n')
        self.assertEqual(ingest(self.db,self.log)['new_events'],1)
        self.assertEqual(ingest(self.db,self.log)['new_events'],0)
        self.assertEqual(len(get_players(self.db)),1)
    def test_append_and_unfinished_line(self):
        self.log.write_text('AdminLog started on 2026-10-14 at 12:00:00\n12:01:00 | pending')
        self.assertEqual(ingest(self.db,self.log)['new_events'],0)
        with self.log.open('a') as f:f.write(' complete\n')
        self.assertEqual(ingest(self.db,self.log)['new_events'],1)
        self.assertEqual(get_events(self.db)[0]['kind'],'unknown')
    def test_rollover(self):
        self.log.write_text('AdminLog started on 2026-10-14 at 23:56:00\n23:59:30 | late\n00:01:00 | early\n')
        self.assertEqual(ingest(self.db,self.log)['new_events'],2)
        self.assertEqual(get_events(self.db)[0]['occurred_at'],'2026-10-15T00:01:00')
    def test_truncation_generation(self):
        self.log.write_text('AdminLog started on 2026-10-14 at 12:00:00\n12:01:00 | initial event is very long\n')
        a=ingest(self.db,self.log)
        self.log.write_text('AdminLog started on 2026-10-15 at 11:00:00\n11:02:00 | shorter\n')
        b=ingest(self.db,self.log)
        self.assertTrue(b['rotated']);self.assertEqual(b['generation'],a['generation']+1)
        self.assertEqual(b['new_events'],1)
    def test_no_date_if_missing(self):
        self.log.write_text('12:01:00 | Player "SYNTH" (id=SYNTHID pos=<1, 2, 3>)\n')
        ingest(self.db,self.log)
        self.assertIsNone(get_events(self.db)[0]['occurred_at'])
    def test_snapshot_not_current(self):
        self.log.write_text('AdminLog started on 2026-10-14 at 12:00:00\n12:01:00 | Player "SYNTH" (id=SYNTHID pos=<1, 2, 3>)\n12:05:00 | Player "SYNTH" (id=SYNTHID pos=<4, 5, 6>)\n')
        ingest(self.db,self.log)
        self.assertEqual(len(get_players(self.db)),1)
        self.assertEqual((get_players(self.db)[0]['x'],get_players(self.db)[0]['z']),(4,5))
    def test_out_of_order_file_import_keeps_newest_observation(self):
        latest=Path(self.tmp.name)/"latest.ADM"
        latest.write_text('AdminLog started on 2026-10-15 at 12:00:00\n12:00:00 | Player "SYNTH" (id=SYNTHID pos=<99, 99, 1>)\n')
        old=Path(self.tmp.name)/"old.ADM"
        old.write_text('AdminLog started on 2026-10-14 at 12:00:00\n12:00:00 | Player "SYNTH" (id=SYNTHID pos=<1, 1, 1>)\n')
        ingest(self.db,latest);ingest(self.db,old)
        self.assertEqual(get_players(self.db)[0]['x'],99)
    def test_servers_isolated(self):
        self.log.write_text('AdminLog started on 2026-10-14 at 12:00:00\n12:01:00 | Player "SYNTH" (id=SYNTHID pos=<1, 2, 3>)\n')
        ingest(self.db,self.log,server='test-a');ingest(self.db,self.log,server='test-b')
        self.assertEqual(len(get_players(self.db,'test-a')),1)
        self.assertEqual(len(get_players(self.db,'test-b')),1)
        self.assertEqual(len(get_players(self.db,'default')),0)

if __name__=='__main__':unittest.main()

# Import ordering must never masquerade as chronological order.
class ChronologicalOrderingTests(unittest.TestCase):
    def test_old_log_imported_later_is_not_first_event(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db = root / 'db.sqlite'
            latest = root / 'latest.ADM'
            earlier = root / 'earlier.ADM'
            latest.write_text('AdminLog started on 2026-10-15 at 12:00:00\n12:03:00 | latest event\n')
            earlier.write_text('AdminLog started on 2026-10-14 at 12:00:00\n12:03:00 | earlier event\n')
            ingest(db, latest)
            ingest(db, earlier)
            self.assertEqual(get_events(db)[0]['occurred_at'],'2026-10-15T12:03:00')



# A Nitrado download replaces the local log atomically (new inode).
class AtomicDownloadRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / "log.ADM"
        self.db = Path(self.tmp.name) / "db.sqlite"

    def replace(self, payload):
        import os
        part = self.log.with_suffix(".part")
        part.write_bytes(payload)
        os.replace(part, self.log)

    def test_atomic_append_preserves_event_ids(self):
        original = (b'AdminLog started on 2026-10-15 at 12:00:00\n'
                    b'12:01:00 | Player "Tester" (id=INTERNAL_ID pos=<1, 2, 3>)\n')
        self.log.write_bytes(original)
        initial = ingest(self.db, self.log)
        self.replace(original + b'12:06:00 | Player "Tester" (id=INTERNAL_ID pos=<2, 3, 4>)\n')
        update = ingest(self.db, self.log)
        self.assertFalse(update["rotated"])
        self.assertEqual(update["new_events"], 1)
        self.assertEqual(initial["generation"], update["generation"])
        self.assertEqual(len(get_events(self.db)), 2)

    def test_rewrite_after_same_prefix_triggers_rotation(self):
        same = (b'AdminLog started on 2026-10-15 at 12:00:00\n'
                + b'12:00:00 | ' + b'A' * 145 + b'\n')
        self.log.write_bytes(same + b'12:01:00 | before\n')
        original = ingest(self.db, self.log)
        self.replace(same + b'12:01:00 | after\n')
        update = ingest(self.db, self.log)
        self.assertTrue(update["rotated"])
        self.assertEqual(update["generation"], original["generation"] + 1)

    def test_legacy_sources_schema_migrates_in_place(self):
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(self.db)) as connection:
            connection.execute("""CREATE TABLE sources (
                server TEXT NOT NULL, path TEXT NOT NULL,
                generation INTEGER NOT NULL DEFAULT 0, offset INTEGER NOT NULL DEFAULT 0,
                device INTEGER NOT NULL DEFAULT 0, inode INTEGER NOT NULL DEFAULT 0,
                prefix BLOB NOT NULL DEFAULT X'', base_date TEXT,
                last_second INTEGER, rollover INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (server,path)
            )""")
        self.log.write_text("AdminLog started on 2026-10-15 at 12:00:00\n12:01:00 | event\n")
        self.assertEqual(ingest(self.db, self.log)["new_events"], 1)
        with closing(sqlite3.connect(self.db)) as connection:
            cols = [r[1] for r in connection.execute("PRAGMA table_info(sources)")]
        self.assertIn("content_hash", cols)

class InplaceRewriteRegressionTests(unittest.TestCase):
    def test_same_inode_same_size_rewrite_generates_new_source_generation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db, log = root / "db.sqlite", root / "active.ADM"
            beginning = (b"AdminLog started on 2026-10-15 at 12:00:00\\n"
                         + b"12:00:00 | " + b"A"*160 + b"\\n")
            log.write_bytes(beginning + b"12:01:00 | before\\n")
            first = ingest(db, log)
            inode = log.stat().st_ino
            with log.open("r+b") as file:
                file.seek(0)
                file.write(beginning + b"12:01:00 | after!\\n")
                file.truncate()
            self.assertEqual(log.stat().st_ino, inode)
            later = ingest(db, log)
            self.assertTrue(later["rotated"])
            self.assertEqual(later["generation"], first["generation"] + 1)
            self.assertEqual(later["new_events"], 1)

    def test_inplace_rewrite_plus_append_not_misread_as_clean_append(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            db, log = root / "db.sqlite", root / "active.ADM"
            beginning = (b"AdminLog started on 2026-10-15 at 12:00:00\\n"
                         + b"12:00:00 | " + b"A"*160 + b"\\n")
            log.write_bytes(beginning + b"12:01:00 | before\\n")
            first = ingest(db, log)
            with log.open("r+b") as file:
                file.seek(0)
                file.write(beginning + b"12:01:00 | after!\\n12:02:00 | new\\n")
                file.truncate()
            later = ingest(db, log)
            self.assertTrue(later["rotated"])
            self.assertEqual(later["generation"], first["generation"] + 1)
            self.assertEqual(later["new_events"], 2)
