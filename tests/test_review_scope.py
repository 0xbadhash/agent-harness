#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from review_scope import (  # noqa: E402
    ScopeBaseline,
    classify_finding,
    is_prose_path,
    is_test_path,
    scope_growth_exceeded,
    should_skip_heavy_review,
)


class TestPaths(unittest.TestCase):
    def test_test_path(self):
        self.assertTrue(is_test_path("tests/test_foo.py"))
        self.assertTrue(is_test_path("src/foo_test.py"))
        self.assertFalse(is_test_path("scripts/review_scope.py"))

    def test_prose_path(self):
        self.assertTrue(is_prose_path(".agents/skills/cross_review/SKILL.md"))
        self.assertFalse(is_prose_path("README.md"))
        self.assertFalse(is_prose_path("docs/SECURITY.md"))
        self.assertFalse(is_prose_path("scripts/x.py"))


class TestClassify(unittest.TestCase):
    def test_in_scope(self):
        self.assertEqual(
            classify_finding(
                introduced_by_diff=True,
                same_owner_boundary=True,
                requires_new_contract=False,
            ),
            "in_scope_blocker",
        )

    def test_follow_up(self):
        self.assertEqual(
            classify_finding(
                introduced_by_diff=False,
                same_owner_boundary=True,
                requires_new_contract=False,
            ),
            "follow_up",
        )

    def test_escalate(self):
        self.assertEqual(
            classify_finding(
                introduced_by_diff=True,
                same_owner_boundary=True,
                requires_new_contract=True,
            ),
            "stop_and_escalate",
        )


class TestSkipAndGrowth(unittest.TestCase):
    def test_skip_prose_only(self):
        b = ScopeBaseline(
            base_ref="a",
            head_ref="b",
            files=[".agents/skills/x/SKILL.md"],
            n_files=1,
            n_insertions=10,
            n_deletions=0,
            non_test_loc=10,
            prose_only=True,
        )
        self.assertTrue(should_skip_heavy_review(b))

    def test_growth(self):
        o = ScopeBaseline("a", "b", ["a.py"], 1, 10, 0, 10, False)
        c = ScopeBaseline("a", "b", ["a.py", "b.py", "c.py"], 3, 50, 0, 50, False)
        self.assertTrue(scope_growth_exceeded(o, c, max_factor=2.0))


if __name__ == "__main__":
    unittest.main()
