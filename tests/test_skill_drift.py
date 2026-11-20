#!/usr/bin/env python3
"""Synthetic skill-drift cases. The worktree manifest check lands in commit 3b."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_skill_drift.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _tree(root: Path, *, install: bool, retrospect_install: bool, extra: str | None, flip: bool) -> None:
    _write(root / "config" / "ship_skills.txt", "demo\n")
    _write(root / "config" / "optional_skills.txt", "retrospect\n")
    _write(root / "skills" / "demo" / "SKILL.md", "same\n")
    _write(root / "skills" / "retrospect" / "SKILL.md", "retro\n")
    if not install:
        return
    demo = "same\n"
    if flip:
        demo = "same!\n"
    _write(root / ".agents" / "skills" / "demo" / "SKILL.md", demo)
    if retrospect_install:
        _write(root / ".agents" / "skills" / "retrospect" / "SKILL.md", "retro\n")
    if extra:
        _write(root / ".agents" / "skills" / extra / "SKILL.md", "extra\n")


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


class TestSkillDrift(unittest.TestCase):
    def test_identical_copy_exits_0(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _tree(root, install=True, retrospect_install=True, extra=None, flip=False)
            result = _run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("skill drift ok", result.stdout)

    def test_byte_flip_exits_1_and_names_diff(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _tree(root, install=True, retrospect_install=True, extra=None, flip=True)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("DIFF demo", result.stdout)

    def test_missing_retrospect_while_install_exists(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _tree(root, install=True, retrospect_install=False, extra=None, flip=False)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("MISSING retrospect", result.stdout)

    def test_absent_install_tree_exits_0(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _tree(root, install=False, retrospect_install=False, extra=None, flip=False)
            result = _run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("skill drift ok", result.stdout)

    def test_extra_directory_exits_1(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _tree(root, install=True, retrospect_install=True, extra="orphan", flip=False)
            result = _run(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("EXTRA orphan", result.stdout)


if __name__ == "__main__":
    unittest.main()
