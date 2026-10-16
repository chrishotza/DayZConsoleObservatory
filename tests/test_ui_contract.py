"""Offline browser-contract regressions (optional Node execution, no browser server)."""
import json
import re
import shutil
import subprocess
import unittest

from dayz_observatory.server import WEB


class FrontendContractTests(unittest.TestCase):
    def test_datetime_filter_uses_real_digit_regex_not_literal_backslashes(self):
        source = (WEB / "app.js").read_text(encoding="utf-8")
        line = next(line.strip() for line in source.splitlines()
                    if line.strip().startswith("const isSecondPrecision="))
        self.assertIn(r"/^\d{4}-\d{2}-\d{2}T", line)
        self.assertNotIn(r"\\d", line)
        self.assertTrue(line.endswith(";"))

    def test_datetime_filter_behaves_correctly_when_node_is_available(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node unavailable; static frontend contract test still applies")
        source = (WEB / "app.js").read_text(encoding="utf-8")
        line = next(line.strip() for line in source.splitlines()
                    if line.strip().startswith("const isSecondPrecision="))
        script = (line + "\nconsole.log(JSON.stringify(["
                  "'2026-10-15T12:34','2026-10-15T12:34:56',"
                  "'not a time','2026-10-15T12:34Z'].map(isSecondPrecision)));")
        proc = subprocess.run([node, "-e", script], text=True, capture_output=True,
                              timeout=10, check=True)
        self.assertEqual(json.loads(proc.stdout), [True, True, False, False])

    def test_timeline_uses_dom_safe_text_rendering_and_disclaimer(self):
        script = (WEB / "app.js").read_text(encoding="utf-8")
        document = (WEB / "index.html").read_text(encoding="utf-8")
        for element in ("incidentStart", "incidentEnd", "incidentSearch", "incidentOutput"):
            self.assertIn('id="' + element + '"', document)
        self.assertIn("Proximity is not proof of interaction", document)
        self.assertIn("root.replaceChildren()", script)
        self.assertNotIn("innerHTML", script)
        self.assertIn("textContent", script)


if __name__ == "__main__":
    unittest.main()
