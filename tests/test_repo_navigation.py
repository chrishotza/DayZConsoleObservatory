"""Keep the compact AI map, version and entrypoints from silently drifting."""
import json
from pathlib import Path
import re
import unittest

from dayz_observatory import __version__


ROOT = Path(__file__).resolve().parents[1]


class RepositoryNavigationTests(unittest.TestCase):
    def test_machine_index_is_parseable_and_matches_actual_release(self):
        index = json.loads((ROOT / "project-index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["version"], __version__)
        version = re.search(r'^version\s*=\s*"([^"]+)"',
                            (ROOT / "pyproject.toml").read_text(), flags=re.MULTILINE)
        self.assertIsNotNone(version)
        self.assertEqual(version.group(1), __version__)

    def test_all_machine_index_paths_exist_inside_repo(self):
        index = json.loads((ROOT / "project-index.json").read_text(encoding="utf-8"))
        paths = list(index["entrypoints"].values())
        for files in index["modules"].values():
            paths.extend(files)
        for name in paths:
            with self.subTest(name=name):
                self.assertNotIn("..", Path(name).parts)
                path = (ROOT / name).resolve()
                self.assertTrue(path.is_relative_to(ROOT.resolve()))
                self.assertTrue(path.exists(), msg=name)

    def test_ai_entrypoint_is_small_and_has_critical_truth_claims(self):
        agent = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertLess(len(agent.encode("utf-8")), 8192)
        for phrase in ("Nitrado", "UNVERIFIED", "loopback", "synthetic", "Windows"):
            self.assertIn(phrase.lower(), agent.lower())
        for name in ("README.md", "README.es.md", "docs/INDEX.md",
                     "docs/GUI_GUIDE.md", "START_HERE.cmd", "launcher.py"):
            self.assertTrue((ROOT / name).exists())

if __name__ == "__main__":
    unittest.main()
