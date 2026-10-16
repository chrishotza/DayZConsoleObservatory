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

    def test_machine_index_ci_matrix_matches_workflow(self):
        """Machine-readable platform claims must match actual CI, not go stale."""
        index = json.loads((ROOT / "project-index.json").read_text(encoding="utf-8"))
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        expected = set(index["validation"]["github_actions"])
        actual = set()
        for job, runner in (("unit-tests", "ubuntu"), ("windows-smoke", "windows"),
                            ("macos-smoke", "macos")):
            header = "  " + job + ":\n"
            self.assertIn(header, workflow, msg=job)
            # Only split at another two-space job header, not at its indented YAML contents.
            section = re.split(r'(?m)^  [A-Za-z0-9_-]+:\s*
            self.assertIn("runs-on: " + runner + "-latest", section)
            matrix = re.search(r'python-version:\s*\[([^\]]+)\]', section)
            self.assertIsNotNone(matrix, msg=job)
            versions = re.findall(r'"(\d+\.\d+)"', matrix.group(1))
            self.assertTrue(versions, msg=job)
            actual.update(runner + " Python " + version for version in versions)
        self.assertEqual(actual, expected)

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
, workflow.split(header, 1)[1], maxsplit=1)[0]
            self.assertIn("runs-on: " + runner + "-latest", section)
            matrix = re.search(r'python-version:\s*\[([^\]]+)\]', section)
            self.assertIsNotNone(matrix, msg=job)
            versions = re.findall(r'"(\d+\.\d+)"', matrix.group(1))
            self.assertTrue(versions, msg=job)
            actual.update(runner + " Python " + version for version in versions)
        self.assertEqual(actual, expected)

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
