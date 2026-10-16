"""Private evidence export and aggregate-only sharing regression suite."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from dayz_observatory.casebook import build_case, save_case, _fingerprint
from dayz_observatory.store import ingest
from dayz_observatory.cli import main

class CasebookTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.db=self.root/'events.sqlite'
        self.adm=self.root/'SECRET.ADM'
        self.adm.write_text('AdminLog started on 2026-10-15 at 12:00:00\n'
            '12:01:00 | Player "PRIVATE_NAME" (id=SECRET_UID) is connected\n'
            '12:04:00 | Player "PRIVATE_NAME" (id=SECRET_UID pos=<129.4, 456.1, 5>)\n'
            '12:08:00 | Player "PRIVATE_NAME" (id=SECRET_UID) has been disconnected\n',encoding='utf8')
        ingest(self.db,self.adm,'PRIVATE_SERVICE')

    def test_aggregate_by_default_contains_no_identity_timestamp_location_or_path(self):
        report=build_case(self.db,'PRIVATE_SERVICE','SECRET_UID')
        self.assertEqual(report['disclosure'],'aggregate-only')
        self.assertEqual(report['event_count'],3)
        self.assertEqual(report['position_observations'],1)
        self.assertEqual(report['session_status_counts'],{'complete':1})
        dumped=json.dumps(report)
        for secret in ['PRIVATE_NAME','SECRET_UID','PRIVATE_SERVICE','SECRET.ADM','2026-10-15','129.4','456.1','12:04:00']:
            self.assertNotIn(secret,dumped)

    def test_private_case_keeps_provenance_and_fingerprints(self):
        report=build_case(self.db,'PRIVATE_SERVICE','SECRET_UID',private=True)
        self.assertEqual(report['disclosure'],'private')
        self.assertEqual(report['subject']['player_id'],'SECRET_UID')
        self.assertEqual(len(report['events']),3)
        self.assertEqual(report['events'][0]['record_fingerprint_sha256'],_fingerprint(report['events'][0]))
        self.assertEqual(len(report['events'][0]['record_fingerprint_sha256']),64)
        self.assertIn('not a cryptographic attestation',report['fingerprint_scope'])

    def test_limit_marks_partial_export(self):
        report=build_case(self.db,'PRIVATE_SERVICE','SECRET_UID',limit=1)
        self.assertEqual(report['event_count'],1)
        self.assertEqual(report['matched_event_count'],3)
        self.assertTrue(report['truncated'])

    def test_invalid_identifier_rejected(self):
        for ident in ['', '\x00', 'x'*257]:
            with self.subTest(ident=repr(ident)),self.assertRaises(ValueError):
                build_case(self.db,'PRIVATE_SERVICE',ident)

    def test_invalid_limits_rejected(self):
        for limit in [-1,0,2001,True,1.0]:
            with self.subTest(limit=limit),self.assertRaises(ValueError):
                build_case(self.db,'PRIVATE_SERVICE','SECRET_UID',limit=limit)

    def test_exclusive_write_and_safe_permissions(self):
        path=self.root/'case.json'
        report=build_case(self.db,'PRIVATE_SERVICE','SECRET_UID')
        save_case(path,report)
        self.assertEqual(json.loads(path.read_text()),report)
        with self.assertRaises(FileExistsError):
            save_case(path,{'overwrite':True})
        self.assertEqual(json.loads(path.read_text()),report)
        if os.name=='posix':
            self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_preexisting_symlink_cannot_be_overwritten(self):
        original=self.root/'target'
        original.write_text('stay')
        alias=self.root/'alias'
        try: alias.symlink_to(original)
        except (OSError,NotImplementedError): self.skipTest('symlinks unavailable')
        with self.assertRaises(OSError):
            save_case(alias,{'key':'value'})
        self.assertEqual(original.read_text(),'stay')

    def test_save_private_never_writes_stdout(self):
        stdout=StringIO()
        with redirect_stdout(stdout):
            save_case(self.root/'private.json',build_case(self.db,'PRIVATE_SERVICE','SECRET_UID',private=True))
        self.assertEqual(stdout.getvalue(),'')

    def test_cli_share_output_excludes_identity(self):
        stdout=StringIO()
        with redirect_stdout(stdout):
            main(['case','SECRET_UID','--db',str(self.db),'--server','PRIVATE_SERVICE',
                  '--out',str(self.root/'share.json')])
        self.assertNotIn('SECRET_UID',stdout.getvalue())
        payload=json.loads((self.root/'share.json').read_text())
        self.assertNotIn('SECRET_UID',json.dumps(payload))
        self.assertEqual(payload['disclosure'],'aggregate-only')

    def test_cli_private_requires_explicit_switch(self):
        stdout=StringIO()
        with redirect_stdout(stdout):
            main(['case','SECRET_UID','--db',str(self.db),'--server','PRIVATE_SERVICE',
                  '--out',str(self.root/'private.json'),'--private'])
        self.assertNotIn('SECRET_UID',stdout.getvalue())
        payload=json.loads((self.root/'private.json').read_text())
        self.assertEqual(payload['subject']['player_id'],'SECRET_UID')

if __name__=='__main__': unittest.main()
