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
    is_large_baseline,
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

    def test_large_by_non_test_loc(self):
        b = ScopeBaseline("a", "b", ["a.py"], 1, 150, 0, 150, False)
        large, detail = is_large_baseline(b)
        self.assertTrue(large)
        self.assertIn("non_test_loc", detail)

    def test_large_by_product_paths(self):
        b = ScopeBaseline("a", "b", ["src/a.py", "src/b.py", "src/c.py"], 3, 10, 0, 10, False)
        large, _ = is_large_baseline(
            b, product_path_count=3, product_prefixes_configured=True
        )
        self.assertTrue(large)
        large2, _ = is_large_baseline(
            b, product_path_count=3, product_prefixes_configured=False
        )
        self.assertFalse(large2)

    def test_large_thresholds_override_kwargs(self):
        b = ScopeBaseline("a", "b", ["a.py"], 1, 50, 0, 50, False)
        # default non_test_loc threshold 150 → not large
        large, _ = is_large_baseline(b)
        self.assertFalse(large)
        large2, detail = is_large_baseline(b, large_non_test_loc=40)
        self.assertTrue(large2)
        self.assertIn("non_test_loc", detail)

    def test_load_thresholds_from_plugin(self):
        import tempfile
        from pathlib import Path

        from review_scope import load_large_thresholds

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agents = root / ".agents"
            agents.mkdir()
            (agents / "product_plugin.yaml").write_text(
                "product_id: t\n"
                "review_scope:\n"
                "  large_files: 20\n"
                "  large_lines: 500\n"
                "  large_non_test_loc: 300\n"
                "  large_product_paths: 5\n",
                encoding="utf-8",
            )
            files_t, lines_t, ntl_t, pp_t = load_large_thresholds(root)
            self.assertEqual((files_t, lines_t, ntl_t, pp_t), (20, 500, 300, 5))


if __name__ == "__main__":
    unittest.main()
