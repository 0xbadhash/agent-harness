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


if __name__ == "__main__":
    unittest.main()
