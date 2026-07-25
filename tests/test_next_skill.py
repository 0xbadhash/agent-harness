#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import next_skill as ns  # noqa: E402
from review_scope import ScopeBaseline  # noqa: E402


def _b(**kwargs):
    defaults = dict(
        base_ref="a",
        head_ref="b",
        files=["scripts/foo.py"],
        n_files=1,
        n_insertions=20,
        n_deletions=0,
        non_test_loc=20,
        prose_only=False,
    )
    defaults.update(kwargs)
    return ScopeBaseline(**defaults)


class TestNextSkill(unittest.TestCase):
    def test_execute_dev_code_requires_code_review(self):
        with mock.patch.object(ns, "build_baseline", return_value=_b()):
            nxt, meta = ns.decide("execute_dev", base="a", head="b", repo=Path("."))
        self.assertEqual(nxt, "/code_review")
        self.assertEqual(meta.get("code_review"), "required")

    def test_execute_dev_prose_skips_to_pr(self):
        b = _b(files=[".agents/skills/x/SKILL.md"], prose_only=True, non_test_loc=5)
        with mock.patch.object(ns, "build_baseline", return_value=b):
            nxt, meta = ns.decide("execute_dev", base="a", head="b", repo=Path("."))
        self.assertEqual(nxt, "/pr_review --validate")
        self.assertEqual(meta.get("code_review"), "skipped")

    def test_code_review_large_to_cross(self):
        b = _b(n_files=10, n_insertions=100, n_deletions=100, non_test_loc=200)
        with mock.patch.object(ns, "build_baseline", return_value=b):
            nxt, _ = ns.decide("code_review", base="a", head="b", repo=Path("."))
        self.assertEqual(nxt, "/cross_review")

    def test_code_review_runtime_to_behavior(self):
        b = _b(files=["src/app.ts"], n_files=2, n_insertions=30, non_test_loc=30)
        with mock.patch.object(ns, "build_baseline", return_value=b):
            nxt, _ = ns.decide("code_review", base="a", head="b", repo=Path("."))
        self.assertEqual(nxt, "/behavior_validator")

    def test_behavior_to_pr(self):
        nxt, _ = ns.decide("behavior_validator", base="a", head="b", repo=Path("."))
        self.assertEqual(nxt, "/pr_review --validate")


if __name__ == "__main__":
    unittest.main()
