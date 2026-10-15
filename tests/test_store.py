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
