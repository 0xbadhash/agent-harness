"""Diff-scoped comment audit used by hard_gates (T2087U item 1)."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_comment_audit as cca  # noqa: E402


def _git(root: Path, *args: str) -> None:
    env = dict(os.environ)
    env.update(
        GIT_AUTHOR_NAME="Test",
        GIT_AUTHOR_EMAIL="test@example.com",
        GIT_COMMITTER_NAME="Test",
        GIT_COMMITTER_EMAIL="test@example.com",
    )
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def _repo(td: str) -> Path:
    root = Path(td)
    _git(root, "init", "-q")
    (root / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    return root


class TestCommentAuditCheck(unittest.TestCase):
    def test_added_history_comment_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = _repo(td)
            with (root / "a.py").open("a", encoding="utf-8") as f:
                f.write("# previously this returned None\nx = 2\n")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "change")
            ok, msgs = cca.check(root, "HEAD~1", "HEAD")
            self.assertFalse(ok)
            self.assertTrue(any("history" in m for m in msgs))

    def test_preexisting_history_comment_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _git(root, "init", "-q")
            (root / "a.py").write_text(
                "# previously this returned None\nx = 1\n", encoding="utf-8"
            )
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "base")
            (root / "a.py").write_text(
                "# previously this returned None\nx = 2\n", encoding="utf-8"
            )
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "change")
            ok, msgs = cca.check(root, "HEAD~1", "HEAD")
            self.assertTrue(ok, msgs)

    def test_clean_diff_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = _repo(td)
            (root / "a.py").write_text("# constraint: keep sorted\nx = 3\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "change")
            ok, msgs = cca.check(root, "HEAD~1", "HEAD")
            self.assertTrue(ok, msgs)


class TestJustificationAudit(unittest.TestCase):
    def test_escape_hatch_comment_fails(self):
        for phrase in (
            "# for now, this is fine",
            "# temporary until the API lands",
            "# works around the flaky client",
            "# safe to ignore",
        ):
            with self.subTest(phrase=phrase):
                self.assertEqual(cca.classify_comment(phrase), "escape_hatch")

    def test_escape_hatch_naming_a_check_passes(self):
        line = "# temporary shim, see scripts/check_repo_hygiene.py"
        self.assertIsNone(cca.classify_comment(line))

    def test_escape_hatch_in_added_diff_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = _repo(td)
            (root / "a.py").write_text("# for now\nx = 2\n", encoding="utf-8")
            _git(root, "add", "-A")
            _git(root, "commit", "-q", "-m", "change")
            ok, msgs = cca.check(root, "HEAD~1", "HEAD")
            self.assertFalse(ok, msgs)
            self.assertTrue(any("escape_hatch" in m for m in msgs), msgs)

    def test_baseline_ratchet(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("# for now\nx = 1\n", encoding="utf-8")
            baseline = root / "baseline.json"
            self.assertEqual(cca.main(["--root", str(root), "--baseline", str(baseline), "--update-baseline"]), 0)
            self.assertEqual(cca.main(["--root", str(root), "--baseline", str(baseline), "--strict"]), 0)
            (root / "b.py").write_text("# safe to ignore\nx = 2\n", encoding="utf-8")
            self.assertEqual(cca.main(["--root", str(root), "--baseline", str(baseline), "--strict"]), 1)

    def test_non_repo_is_not_a_ship(self):
        with tempfile.TemporaryDirectory() as td:
            ok, msgs = cca.check(Path(td), "HEAD~1", "HEAD")
            self.assertTrue(ok, msgs)


if __name__ == "__main__":
    unittest.main()
