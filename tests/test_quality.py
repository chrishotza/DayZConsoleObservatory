import json
import tempfile
import unittest
from pathlib import Path
from dayz_observatory.store import ingest, get_quality_report
from dayz_observatory.cli import main
from unittest.mock import patch
from io import StringIO


class QualityReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name)/'db.sqlite'
        self.log = Path(self.tmp.name)/'dayz.ADM'

    def test_empty_report_is_valid(self):
        report = get_quality_report(self.db)
        self.assertEqual(report['events'],0)
        self.assertEqual(report['position_observations'],0)
        self.assertIsNone(report['last_observed'])
        self.assertEqual(report['event_types'],[])

    def test_evidence_counts_and_isolation(self):
        self.log.write_text('AdminLog started on 2026-10-14 at 12:00:00\n'
            '12:01:00 | Player "One" (id=ONE pos=<1, 2, 3>)\n'
            '12:02:00 | unknown event\n')
        ingest(self.db,self.log,'xbox-a')
        report = get_quality_report(self.db,'xbox-a')
        self.assertEqual(report['events'],2)
        self.assertEqual(report['known_players'],1)
        self.assertEqual(report['position_observations'],1)
        self.assertEqual(report['unclassified_events'],1)
        self.assertEqual(report['dated_events'],2)
        self.assertEqual(report['imported_sources'],1)
        self.assertEqual(get_quality_report(self.db,'xbox-b')['events'],0)

    def test_undated_records_not_faked(self):
        self.log.write_text('12:02:00 | unknown event\n')
        ingest(self.db,self.log)
        self.assertEqual(get_quality_report(self.db)['undated_events'],1)
        self.assertIsNone(get_quality_report(self.db)['last_observed'])

    def test_audit_command_prints_machine_readable_json(self):
        with patch('sys.stdout',new_callable=StringIO) as capture:
            main(['audit','--db',str(self.db)])
        self.assertEqual(json.loads(capture.getvalue())['events'],0)

if __name__=='__main__':
    unittest.main()
