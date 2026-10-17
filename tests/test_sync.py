"""Offline Nitrado log synchronization verification."""
import errno
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from dayz_observatory.sync import sync_once, _remote_signature, STATE_FILE
from dayz_observatory.nitrado import NitradoClient, NitradoError
from dayz_observatory.store import get_quality_report

ROOT = "/games/operator/noftp/dayzxb/config"
SAMPLE = (b"*** AdminLog started on 2026-10-15 at 12:00:00\n"
          b'12:01:00 | Player "Tester" (id=ABC123 pos=<120, 150, 5>)\n')

class FakeAPI:
    _service_id = staticmethod(NitradoClient._service_id)
    def __init__(self):
        self.entries = [self.entry("log.ADM", 10, SAMPLE)]
        self.content = {ROOT + "/log.ADM": SAMPLE}
        self.calls = []
        self.fail = False
    @staticmethod
    def entry(name, modified, contents, metadata=True):
        result = {"name": name, "path": ROOT + "/" + name, "type": "file"}
        if metadata:
            result.update({"modified_at": modified, "size": len(contents)})
        return result
    def discover_log_directory(self, sid):
        self.calls.append("discover")
        return ROOT, {"game": "dayzxb"}
    def list_logs(self, sid, directory):
        self.calls.append("list")
        return list(self.entries)
    def download_log(self, sid, remote, path, directory):
        self.calls.append(remote)
        if self.fail:
            raise NitradoError("secret token should not escape")
        Path(path).write_bytes(self.content[remote])
        return Path(path)

class SyncTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.api = FakeAPI()
        self.db = self.root / "audit.db"
    def run_sync(self, **options):
        return sync_once(self.api, 42, output=self.root / "logs", db=self.db, **options)

    def test_cache_and_deduplicate(self):
        first = self.run_sync()
        self.assertEqual(first["downloaded"], 1)
        self.assertEqual(first["files"][0]["new_events"], 1)
        second = self.run_sync()
        self.assertEqual(second["cached"], 1)
        self.assertEqual(second["files"][0]["new_events"], 0)
        self.assertEqual(self.api.calls.count(ROOT + "/log.ADM"), 1)

    def test_rebuild_database_from_cached_file(self):
        self.run_sync()
        self.db.unlink()
        report = self.run_sync()
        self.assertEqual(report["cached"], 1)
        self.assertEqual(report["files"][0]["new_events"], 1)

    def test_changed_remote_file_generates_new_events(self):
        self.run_sync()
        newer = SAMPLE.replace(b"ABC123", b"XYZ123")
        self.api.content[ROOT + "/log.ADM"] = newer
        self.api.entries = [self.api.entry("log.ADM", 11, newer)]
        report = self.run_sync()
        self.assertEqual(report["downloaded"], 1)
        self.assertEqual(report["files"][0]["new_events"], 1)
        self.assertEqual(get_quality_report(self.db, "42")["events"], 2)

    def test_no_remote_metadata_disables_cache(self):
        self.api.entries = [self.api.entry("log.ADM", 10, SAMPLE, False)]
        self.run_sync()
        self.run_sync()
        self.assertEqual(self.api.calls.count(ROOT + "/log.ADM"), 2)

    def test_dry_run_never_writes(self):
        report = self.run_sync(dry_run=True)
        self.assertEqual(report["mode"], "dry-run")
        self.assertFalse((self.root / "logs").exists())
        self.assertFalse(self.db.exists())
        self.assertEqual(report["files"][0]["action"], "download")

    def test_dry_run_correctly_predicts_cache(self):
        self.run_sync()
        self.assertEqual(self.run_sync(dry_run=True)["files"][0]["action"], "cached")

    def test_force_and_tampering_invalidate_cache(self):
        self.run_sync()
        path = self.root / "logs" / "42" / "log.ADM"
        path.write_bytes(b"x" * len(SAMPLE))
        self.assertEqual(self.run_sync()["downloaded"], 1)
        self.assertEqual(path.read_bytes(), SAMPLE)
        self.assertEqual(self.run_sync(force=True)["downloaded"], 1)

    def test_rotation_window(self):
        older = SAMPLE.replace(b"ABC123", b"OLD123")
        middle = SAMPLE.replace(b"ABC123", b"MID123")
        self.api.entries = [
            self.api.entry("old.ADM", 10, older),
            self.api.entry("new.ADM", 12, SAMPLE),
            self.api.entry("middle.ADM", 11, middle),
        ]
        self.api.content = {e["path"]: d for e, d in zip(self.api.entries, [older, SAMPLE, middle])}
        report = self.run_sync(max_files=2)
        self.assertEqual([r["name"] for r in report["files"]], ["new.ADM", "middle.ADM"])
        self.assertEqual(get_quality_report(self.db, "42")["events"], 2)

    def test_rpt_is_opt_in(self):
        self.api.entries.append(self.api.entry("log.RPT", 11, b"private identifier"))
        self.api.content[ROOT + "/log.RPT"] = b"private identifier"
        self.run_sync()
        self.assertNotIn(ROOT + "/log.RPT", self.api.calls)
        self.run_sync(include_rpt=True)
        self.assertIn(ROOT + "/log.RPT", self.api.calls)

    def test_reject_bad_remote_entries(self):
        self.api.entries = [{"name": "../secret.ADM", "path": ROOT + "/../secret.ADM"}]
        report = self.run_sync()
        self.assertEqual(len(report["errors"]), 1)

    def test_reject_symlink_destination_without_os_privileges(self):
        """Exercise the real rejection logic even on locked-down Windows runners."""
        root = self.root / "logs" / "42"
        root.mkdir(parents=True)
        destination = root / "log.ADM"
        # Mock the filesystem's classification result, not Path equality:
        # Windows (and Python 3.14) can normalize/resolve path instances
        # differently from the original test's guessed path.
        original_is_symlink = type(destination).is_symlink

        def classify(path):
            # The sync state file should still be checked normally.
            # Filename identity is stable across Windows drive resolution.
            return path.name == "log.ADM" or original_is_symlink(path)

        with patch.object(type(destination), "is_symlink", autospec=True,
                          side_effect=classify) as checker:
            report = self.run_sync()

        self.assertTrue(
            any(call.args and call.args[0].name == "log.ADM" for call in checker.call_args_list),
            "Synchronization must inspect the destination for symlinks",
        )
        self.assertEqual(len(report["errors"]), 1)
        self.assertIn("symlink", report["errors"][0].lower())
        self.assertNotIn(ROOT + "/log.ADM", self.api.calls)
        self.assertFalse(destination.exists())
        self.assertFalse(self.db.exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_reject_symlink_destination(self):
        """Real OS link test: skip only when the OS denies creating test links."""
        root = self.root / "logs" / "42"
        root.mkdir(parents=True)
        private = self.root / "private.txt"
        private.write_text("original")
        try:
            (root / "log.ADM").symlink_to(private)
        except NotImplementedError:
            self.skipTest("OS cannot create symlinks")
        except OSError as exc:
            # Windows standard accounts commonly lack SeCreateSymbolicLinkPrivilege
            # (WinError 1314). Never swallow unrelated I/O failures.
            permitted_skip = (getattr(exc, "winerror", None) == 1314
                              or exc.errno in (errno.EPERM, errno.EACCES))
            if permitted_skip:
                self.skipTest("OS denies creating test symlinks (no user privilege)")
            raise
        report = self.run_sync()
        self.assertEqual(len(report["errors"]), 1)
        self.assertIn("symlink", report["errors"][0].lower())
        self.assertEqual(private.read_text(), "original")
        self.assertNotIn(ROOT + "/log.ADM", self.api.calls)

    def test_errors_do_not_leak_tokens(self):
        self.api.fail = True
        report = self.run_sync()
        self.assertFalse(report["files"])
        self.assertNotIn("secret token", str(report))
        self.assertFalse((self.root / "logs" / "42" / STATE_FILE).exists())

    def test_invalid_metadata(self):
        self.assertIsNone(_remote_signature({"size": True, "modified_at": 12}))
        self.assertIsNone(_remote_signature({"size": 7, "modified_at": None}))
        self.assertEqual(_remote_signature({"size": "7", "modified_at": "today"})["size"], "7")

    def test_invalid_file_limit(self):
        for value in (0, -1, 21, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_sync(max_files=value)
