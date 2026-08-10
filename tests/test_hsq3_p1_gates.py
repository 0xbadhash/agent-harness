#!/usr/bin/env python3
"""HSQ-3 P1: path tests, lockfile audit, red/green cmds."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_changed_path_tests as pt  # noqa: E402
import check_lockfile_audit as la  # noqa: E402
import check_red_green_cmds as rg  # noqa: E402


class TestPathTests(unittest.TestCase):
    def test_ac_1_missing_test(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "scripts" / "foo_module.py").write_text("x=1\n", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "test_other.py").write_text(
                "def test_x():\n    assert True\n", encoding="utf-8"
            )
            (root / "PR_DRAFT.md").write_text("**Spec waiver:** chore\n", encoding="utf-8")
            with mock.patch.object(pt, "_changed", return_value=["scripts/foo_module.py"]):
                ok, msgs = pt.check(root, "A", "B", root / "PR_DRAFT.md")
            self.assertFalse(ok)
            self.assertTrue(any("foo_module" in m for m in msgs))

    def test_ac_2_untested_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts").mkdir()
            (root / "scripts" / "foo_module.py").write_text("x=1\n", encoding="utf-8")
            (root / "PR_DRAFT.md").write_text(
                "## Untested paths\n| scripts/foo_module.py | glue only |\n",
                encoding="utf-8",
            )
            with mock.patch.object(pt, "_changed", return_value=["scripts/foo_module.py"]):
                ok, msgs = pt.check(root, "A", "B", root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)


class TestLockAudit(unittest.TestCase):
    def test_ac_3_no_lockfile(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(la, "_changed", return_value=["scripts/x.py"]):
                ok, msgs = la.check(root, "A", "B")
            self.assertTrue(ok)
            self.assertTrue(any("no lockfile" in m for m in msgs))


class TestRedGreen(unittest.TestCase):
    def test_ac_4_red_must_fail(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text(
                "## Red-proof\nred_cmd: true\ngreen_cmd: true\n",
                encoding="utf-8",
            )
            ok, msgs = rg.check(root, root / "PR_DRAFT.md")
            self.assertFalse(ok)

    def test_ac_5_tdd_na(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text(
                "## Red-proof\nTDD N/A docs-only\n",
                encoding="utf-8",
            )
            ok, msgs = rg.check(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)

    def test_ac_6_good_cmds(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text(
                "## Red-proof\nred_cmd: false\ngreen_cmd: true\n",
                encoding="utf-8",
            )
            ok, msgs = rg.check(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)


if __name__ == "__main__":
    unittest.main()
