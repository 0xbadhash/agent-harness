#!/usr/bin/env python3
"""Edit guard: protected paths; fix-task must not rewrite tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_edit_guard as eg  # noqa: E402


class TestEditGuard(unittest.TestCase):
    def test_protected_env_fails(self):
        with mock.patch.object(eg, "_diff_names", return_value=[".env", "src/app.py"]):
            ok, msgs = eg.check(ROOT, fix_task=False)
        self.assertFalse(ok, msgs)
        self.assertTrue(any(".env" in m for m in msgs), msgs)

    def test_fix_task_blocks_test_rewrite(self):
        with mock.patch.object(
            eg, "_diff_names", return_value=["scripts/foo.py", "tests/test_foo.py"]
        ):
            ok, msgs = eg.check(ROOT, fix_task=True)
        self.assertFalse(ok, msgs)
        self.assertTrue(any("must not rewrite tests" in m for m in msgs), msgs)

    def test_normal_diff_ok(self):
        with mock.patch.object(eg, "_diff_names", return_value=["scripts/foo.py"]):
            ok, msgs = eg.check(ROOT, fix_task=False)
        self.assertTrue(ok, msgs)

    def test_scripts_test_helper_is_not_a_test_file(self):
        self.assertFalse(eg._is_test("scripts/test_trigger_schedule.py"))
        self.assertTrue(eg._is_test("tests/test_foo.py"))

    def test_chore_draft_mentioning_hotfix_is_not_fix_task(self):
        import tempfile
        from pathlib import Path as P

        with tempfile.TemporaryDirectory() as tmp:
            td = P(tmp)
            (td / "PR_DRAFT.md").write_text(
                "**Spec waiver:** chore\n\nFollow-on to a prior hotfix.\n",
                encoding="utf-8",
            )
            self.assertFalse(eg._fix_task_from_draft(td))
            (td / "PR_DRAFT.md").write_text(
                "**Spec waiver:** hotfix\n", encoding="utf-8"
            )
            self.assertTrue(eg._fix_task_from_draft(td))


if __name__ == "__main__":
    unittest.main()
