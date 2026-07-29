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

    def test_pr_review_skips_infra_without_skill(self):
        nxt, meta = ns.decide("pr_review", base="a", head="b", repo=ROOT)
        self.assertEqual(nxt, "/release_mgmt")
        self.assertEqual(meta.get("infra"), "skipped")

    def test_pr_review_suggests_vps_when_skill_present(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skill = root / ".agents" / "skills" / "vps_infra_ops"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# vps\n", encoding="utf-8")
            nxt, meta = ns.decide("pr_review", base="a", head="b", repo=root)
        self.assertEqual(nxt, "/vps_infra_ops --verify")
        self.assertEqual(meta.get("infra"), "required")

    def test_pr_review_skip_infra_flag(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            skill = root / ".agents" / "skills" / "vps_infra_ops"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# vps\n", encoding="utf-8")
            nxt, meta = ns.decide(
                "pr_review", base="a", head="b", repo=root, skip_infra=True
            )
        self.assertEqual(nxt, "/release_mgmt")
        self.assertEqual(meta.get("infra"), "skipped")

    def test_vps_infra_to_release(self):
        nxt, _ = ns.decide("vps_infra_ops", base="a", head="b", repo=ROOT)
        self.assertEqual(nxt, "/release_mgmt")

    def test_sync_docs_suggests_qa_when_forced(self):
        nxt, meta = ns.decide(
            "sync_docs", base="a", head="b", repo=ROOT, force_qa=True
        )
        self.assertEqual(nxt, "/qa_campaign")
        self.assertEqual(meta.get("qa"), "suggested")

    def test_sync_docs_skip_qa(self):
        nxt, meta = ns.decide(
            "sync_docs", base="a", head="b", repo=ROOT, skip_qa=True
        )
        self.assertEqual(nxt, "(done)")
        self.assertEqual(meta.get("qa"), "skipped")

    def test_qa_campaign_to_done(self):
        nxt, _ = ns.decide("qa_campaign", base="a", head="b", repo=ROOT)
        self.assertEqual(nxt, "(done)")

    def test_empty_after_raises(self):
        with self.assertRaises(ValueError):
            ns.decide("", base="a", head="b", repo=ROOT)
        with self.assertRaises(ValueError):
            ns.decide("   ", base="a", head="b", repo=ROOT)

    def test_unknown_after_does_not_echo_slash(self):
        nxt, meta = ns.decide("not_a_ship_skill", base="a", head="b", repo=ROOT)
        self.assertTrue(nxt.startswith("(unknown"))
        self.assertIn("unknown", meta.get("reason", ""))

    def test_commented_require_vps_does_not_trigger(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agents = root / ".agents"
            agents.mkdir(parents=True)
            (agents / "product_plugin.yaml").write_text(
                "# require_vps_infra: true\n"
                "product_path_prefixes:\n"
                "  - src\n",
                encoding="utf-8",
            )
            nxt, meta = ns.decide("pr_review", base="a", head="b", repo=root)
        self.assertEqual(nxt, "/release_mgmt")
        self.assertEqual(meta.get("infra"), "skipped")

    def test_infra_required_block_triggers(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agents = root / ".agents"
            agents.mkdir(parents=True)
            (agents / "product_plugin.yaml").write_text(
                "infra:\n  required: true\n",
                encoding="utf-8",
            )
            nxt, meta = ns.decide("pr_review", base="a", head="b", repo=root)
        self.assertEqual(nxt, "/vps_infra_ops --verify")
        self.assertEqual(meta.get("infra"), "required")


if __name__ == "__main__":
    unittest.main()
