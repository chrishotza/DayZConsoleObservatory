"""Deterministic Nitrado end-to-end regression: no external network."""
from __future__ import annotations
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from urllib.request import Request

from dayz_observatory.cli import main
from dayz_observatory.selftest import _SyntheticTransport, SelfTestError, run_selftest


class OfflineSelfTest(unittest.TestCase):
    def test_end_to_end_uses_no_external_opener(self):
        with patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("NETWORK FORBIDDEN")):
            result = run_selftest()
        self.assertEqual(result["result"], "passed")
        self.assertEqual(len(result["tests"]), 8)
        self.assertTrue(all(result["tests"].values()))
        self.assertFalse(result["used_real_network"])

    def test_cli_no_real_token_required_or_disclosed(self):
        stdout = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), redirect_stdout(stdout):
            main(["selftest"])
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["result"], "passed")
        for secret in ("424242", "OFFLINE_FIXTURE_NO_AUTH", "synthetic-one-use", "SYNTHETIC_ID_001", "/games/"):
            self.assertNotIn(secret, stdout.getvalue())

    def test_simulator_rejects_unexpected_hosts(self):
        transport = _SyntheticTransport()
        for url in ("https://example.org/file", "http://api.nitrado.net/",
                    "https://api.nitrado.net/services/1/gameservers"):
            with self.subTest(url=url), self.assertRaises(SelfTestError):
                transport.open(Request(url))

    def test_no_bearer_forwarded_to_signed_download(self):
        url = "https://files.nitrado.net/offline-fixture?token=synthetic-one-use"
        with self.assertRaises(SelfTestError):
            _SyntheticTransport().open(Request(url, headers={"Authorization": "Bearer SECRET"}))

    def test_environment_token_is_not_consumed(self):
        with patch.dict(os.environ, {"NITRADO_TOKEN": "REAL_USER_SECRET"}):
            self.assertNotIn("REAL_USER_SECRET", json.dumps(run_selftest()))

if __name__ == "__main__":
    unittest.main()
