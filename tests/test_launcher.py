"""No-install launcher smoke test, including on Windows CI."""
import subprocess
import sys
from pathlib import Path
import unittest


class LauncherTests(unittest.TestCase):
    def test_launcher_check_runs_without_port_or_browser(self):
        root = Path(__file__).resolve().parents[1]
        code = subprocess.run([sys.executable, str(root / "launcher.py"), "--check"],
                              text=True, capture_output=True, timeout=15)
        self.assertEqual(code.returncode, 0, msg=code.stderr)
        self.assertIn("no network used", code.stdout.lower())

    def test_windows_double_click_file_exists(self):
        root = Path(__file__).resolve().parents[1]
        file = root / "START_HERE.cmd"
        self.assertTrue(file.is_file())
        self.assertIn("launcher.py", file.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
