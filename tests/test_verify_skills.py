"""Unit tests for verify_skills helpers."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent


def _load_verify():
    path = HARNESS / "scripts" / "verify_skills.py"
    spec = importlib.util.spec_from_file_location("verify_skills", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["verify_skills"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestVerifySkills(unittest.TestCase):
    def test_skills_root_harness(self) -> None:
        m = _load_verify()
        root = m._skills_root(HARNESS)
        self.assertIsNotNone(root)
        assert root is not None
        self.assertTrue((root / "execute_dev" / "SKILL.md").is_file())

    def test_missing_ship_fails(self) -> None:
        m = _load_verify()
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            skills = repo / ".agents" / "skills" / "only_foo"
            skills.mkdir(parents=True)
            (skills / "SKILL.md").write_text(
                "---\nname: only_foo\ndescription: x\n---\n# x\n",
                encoding="utf-8",
            )
            # ship list requires execute_dev etc.
            rc = m.verify(repo, require_ship=True)
            self.assertEqual(rc, 1)

    def test_complete_minimal_ship_ok(self) -> None:
        m = _load_verify()
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ship = m._load_ship_list(HARNESS)
            for name in ship:
                d = repo / ".agents" / "skills" / name
                d.mkdir(parents=True)
                (d / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test skill for {name}\n---\n"
                    f"# {name}\nSee policy/AGENT_REFERENCE.md\n",
                    encoding="utf-8",
                )
            # copy ship list into product policy
            pol = repo / ".agents" / "policy"
            pol.mkdir(parents=True)
            (pol / "ship_skills.txt").write_text(
                (HARNESS / "config" / "ship_skills.txt").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            rc = m.verify(repo, require_ship=True)
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
