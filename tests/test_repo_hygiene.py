"""Pristine-garden hygiene: scratch artifacts and dirty tree fail the gate."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_repo_hygiene as crh  # noqa: E402


class TestScratchArtifacts(unittest.TestCase):
    def test_each_scratch_pattern_fails(self):
        names = [
            "x.bak-1",
            "x.orig",
            "x.rej",
            ".coverage",
            ".coverage.abc123",
            ".venv-oldbak",
            "signal-cli-canary-1",
        ]
        for name in names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / name).write_text("scratch", encoding="utf-8")
                ok, msgs = crh.check(root)
                self.assertFalse(ok, msgs)
                self.assertTrue(any("scratch artifact" in m for m in msgs), msgs)
                self.assertTrue(any(name in m for m in msgs), msgs)

    def test_nested_scratch_artifact_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            nested = root / "config" / "deep"
            nested.mkdir(parents=True)
            (nested / "runtime.yaml.bak-t1").write_text("x", encoding="utf-8")
            ok, msgs = crh.check(root)
            self.assertFalse(ok, msgs)

    def test_skip_dirs_are_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for skip in (".git", ".venv", ".agents", "node_modules", "__pycache__"):
                d = root / skip
                d.mkdir()
                (d / "x.bak-1").write_text("x", encoding="utf-8")
            ok, msgs = crh.check(root)
            self.assertTrue(ok, msgs)

    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "README.md").write_text("ok\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "check.py").write_text("x = 1\n", encoding="utf-8")
            ok, msgs = crh.check(root)
            self.assertTrue(ok, msgs)


class TestDirtyTree(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_dirty_repo_fails_when_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._git(root, "init", "-q")
            (root / "tracked.txt").write_text("one\n", encoding="utf-8")
            self._git(root, "add", "tracked.txt")
            self._git(
                root,
                "-c",
                "user.email=t@example.com",
                "-c",
                "user.name=test",
                "commit",
                "-q",
                "-m",
                "init",
            )
            (root / "untracked.txt").write_text("two\n", encoding="utf-8")
            ok, msgs = crh.check(root, require_clean=True)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("uncommitted" in m for m in msgs), msgs)

            self._git(root, "add", "untracked.txt")
            self._git(
                root,
                "-c",
                "user.email=t@example.com",
                "-c",
                "user.name=test",
                "commit",
                "-q",
                "-m",
                "second",
            )
            ok, msgs = crh.check(root, require_clean=True)
            self.assertTrue(ok, msgs)

    def test_non_repo_is_a_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ok, msgs = crh.check(root, require_clean=True)
            self.assertTrue(ok, msgs)
            self.assertTrue(any(m.startswith("warn:") for m in msgs), msgs)

    def test_dirty_check_off_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._git(root, "init", "-q")
            (root / "untracked.txt").write_text("two\n", encoding="utf-8")
            ok, msgs = crh.check(root)
            self.assertTrue(ok, msgs)


if __name__ == "__main__":
    unittest.main()
