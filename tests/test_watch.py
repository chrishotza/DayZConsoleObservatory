"""No-network tests for foreground polling; no DayZ and no credentials."""
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from dayz_observatory.watch import watch_foreground
from dayz_observatory.cli import main


class WatchTests(unittest.TestCase):
    def run_fake(self, sync=None, max_cycles=2, interval=60):
        tick, reports, sleeps = [0.0], [], []
        def clock():
            return tick[0]
        def sleep(n):
            sleeps.append(n)
            tick[0] += n
        def default(*a, **kw):
            tick[0] += 2
            return {"errors": [], "downloaded": 1, "cached": 0, "selected_files": 2}
        result = watch_foreground(object(), 42, output="SECRET_PATH", db="SECRET_DB",
                                  max_cycles=max_cycles, interval=interval,
                                  sync_fn=sync or default, sleep_fn=sleep,
                                  monotonic_fn=clock, on_cycle=reports.append)
        return result, reports, sleeps

    def test_start_to_start_interval(self):
        result, reports, sleeps = self.run_fake()
        self.assertEqual(sleeps, [58.0])
        self.assertEqual(result, {"status": "completed", "cycles": 2})
        self.assertEqual([x["status"] for x in reports], ["ok", "ok"])

    def test_three_errors_stop_without_secret_leaks(self):
        def broken(*a, **kw):
            raise RuntimeError("TOKEN=secret /games/private/12345")
        result, reports, sleeps = self.run_fake(sync=broken, max_cycles=10)
        self.assertEqual(result["status"], "stopped_after_errors")
        self.assertEqual(result["cycles"], 3)
        self.assertEqual(len(sleeps), 2)
        self.assertNotIn("secret", json.dumps(reports))
        self.assertEqual(reports[0]["error_category"], "remote_service")

    def test_partial_failures_halt(self):
        def partial(*a, **kw):
            return {"errors": ["/games/private"], "downloaded": 1, "cached": 0, "selected_files": 1}
        result, reports, _ = self.run_fake(sync=partial, max_cycles=8)
        self.assertEqual(result["status"], "stopped_after_errors")
        self.assertEqual(reports[0]["errors"], 1)
        self.assertNotIn("/games/private", str(reports))

    def test_success_resets_failure_counter(self):
        attempts = [0]
        def sometimes(*a, **kw):
            attempts[0] += 1
            if attempts[0] % 2:
                raise OSError("private path")
            return {"errors": [], "downloaded": 1, "cached": 0, "selected_files": 1}
        result, reports, _ = self.run_fake(sync=sometimes, max_cycles=4)
        self.assertEqual(result["status"], "completed")
        self.assertEqual([r["status"] for r in reports], ["error", "ok", "error", "ok"])

    def test_ignore_private_sync_fields(self):
        def private(*a, **kw):
            return {"errors": [], "downloaded": 1, "selected_files": 2, "cached": 1,
                    "service_id": 999999, "files": [{"name": "SECRET.ADM"}]}
        _, reports, _ = self.run_fake(sync=private, max_cycles=1)
        self.assertNotIn("999999", str(reports))
        self.assertNotIn("SECRET", str(reports))

    def test_invalid_config_never_calls_sync(self):
        for field, bad in [("interval", 59), ("interval", True), ("interval", 86401),
                           ("max_cycles", 0), ("max_cycles", True),
                           ("max_files", 0), ("service_id", -2)]:
            with self.subTest(field=field, bad=bad):
                args = {"api": object(), "service_id": 5, "output": "x", "db": "x",
                        "sync_fn": lambda *a, **kw: self.fail("sync should not run"), "max_cycles": 1}
                args[field] = bad
                with self.assertRaises(ValueError):
                    watch_foreground(**args)

    def test_one_cycle_never_sleeps(self):
        result, _, sleeps = self.run_fake(max_cycles=1)
        self.assertEqual(result["cycles"], 1)
        self.assertEqual(sleeps, [])

    def test_cli_watch_displays_aggregate_only(self):
        calls = []
        def fake_watch(*args, **kwargs):
            calls.append(kwargs)
            kwargs["on_cycle"]({"cycle": 1, "status": "ok", "downloaded": 0, "cached": 1,
                                "selected_files": 1, "errors": 0, "dry_run": True})
            return {"status": "completed", "cycles": 1}
        output = io.StringIO()
        with patch("dayz_observatory.cli.NitradoClient", return_value=object()), \
             patch("dayz_observatory.cli.watch_foreground", side_effect=fake_watch), redirect_stdout(output):
            main(["nitrado", "12345678", "--watch", "--cycles", "1", "--dry-run", "--interval", "60"])
        self.assertEqual(calls[0]["interval"], 60)
        self.assertTrue(calls[0]["dry_run"])
        self.assertNotIn("12345678", output.getvalue())
        self.assertEqual(json.loads(output.getvalue().splitlines()[0])["cached"], 1)


if __name__ == "__main__":
    unittest.main()
