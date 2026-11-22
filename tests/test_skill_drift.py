#!/usr/bin/env python3
"""Skill drift checker, manifest lines, and the install-copy sync."""
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

    def test_worktree_contains_manifest_lines(self):
        skills = ROOT / "skills"
        blobs = {
            p.parent.name: p.read_text(encoding="utf-8")
            for p in skills.glob("*/SKILL.md")
        }
        for name in ("code_review", "pr_review", "release_mgmt", "sync_docs"):
            self.assertIn("model: none", blobs[name])
        self.assertIn("model: grok-4.7", blobs["spec"])
        self.assertIn("reasoning_effort: high", blobs["spec"])
        self.assertIn("model: grok-4.7", blobs["execute_dev"])
        self.assertIn("reasoning_effort: high", blobs["execute_dev"])
        self.assertIn(
            "Else harness: first open row in `.agents/BACKLOG.md`.",
            blobs["execute_dev"],
        )
        self.assertIn("always ask user before inserting", blobs["agent_transcript"])
        self.assertIn("fail closed on secrets", blobs["agent_transcript"])
        self.assertIn(
            "Ops/debug only — not a ship FSM step.",
            blobs["session_viewer"],
        )
        self.assertTrue((skills / "retrospect" / "SKILL.md").is_file())
        self.assertTrue((skills / "challenge" / "SKILL.md").is_file())
        challenge_lines = blobs["challenge"].splitlines()
        self.assertIn(
            "python3 scripts/challenge.py --proposal path/to/proposal.md",
            challenge_lines,
        )
        self.assertIn(
            "python3 ~/agent-harness/scripts/challenge.py --proposal path/to/proposal.md --root <product-root>",
            challenge_lines,
        )
        self.assertIn(
            "python3 scripts/challenge.py --proposal path/to/proposal.md --decision path/to/decision.md",
            challenge_lines,
        )
        self.assertIn("z-ai-glm-5-3-flash", blobs["challenge"])
        self.assertIn("ask_glm.py", blobs["challenge"])
        self.assertIn("deepseek-v4-flash", blobs["challenge"])
        self.assertIn("Venice", blobs["challenge"])
        self.assertNotIn("audit_repo", blobs["sweep"])

    def test_sync_refuses_unlisted_extra_dir(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import sync_installed_skills as sync_mod  # noqa: E402

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(root / "skills" / "demo" / "SKILL.md", "same\n")
            _write(root / ".agents" / "skills" / "orphan" / "SKILL.md", "extra\n")
            code = sync_mod.sync(root, [])
            self.assertEqual(code, 0)
            self.assertTrue((root / ".agents" / "skills" / "orphan" / "SKILL.md").is_file())
            self.assertEqual(
                (root / ".agents" / "skills" / "demo" / "SKILL.md").read_text(encoding="utf-8"),
                "same\n",
            )
            refused = sync_mod.sync(root, ["demo"])
            self.assertEqual(refused, 1)
            self.assertTrue((root / "skills" / "demo" / "SKILL.md").is_file())
            gone = sync_mod.sync(root, ["orphan"])
            self.assertEqual(gone, 0)
            self.assertFalse((root / ".agents" / "skills" / "orphan").exists())


if __name__ == "__main__":
    unittest.main()
