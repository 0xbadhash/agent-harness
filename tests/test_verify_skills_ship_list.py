#!/usr/bin/env python3
"""AC map: skill portfolio slim — ship_skills no longer requires removed skills."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestShipSkillsSlim(unittest.TestCase):
    def test_ac_1_through_ac_7_required_set(self):
        text = (ROOT / "config" / "ship_skills.txt").read_text(encoding="utf-8")
        required = {
            "spec",
            "execute_dev",
            "code_review",
            "cross_review",
            "behavior_validator",
            "pr_review",
            "release_mgmt",
            "sync_docs",
            "plan_review",
            "sweep",
            "night_shift",
            "handoff",
        }
        lines = [
            ln.strip()
            for ln in text.splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        for name in required:
            self.assertIn(name, lines)
        for gone in (
            "feedback",
            "plan_backend",
            "audit_repo",
            "test_automation",
            "qa_campaign",
            "retrospect",
            "audit_harness",
        ):
            self.assertNotIn(gone, lines)

    def test_ac_removed_dirs(self):
        for gone in ("feedback", "plan_backend", "audit_repo", "test_automation"):
            self.assertFalse((ROOT / "skills" / gone).is_dir(), gone)

    def test_ac_optional_list(self):
        opt = (ROOT / "config" / "optional_skills.txt").read_text(encoding="utf-8")
        for name in (
            "agent_transcript",
            "session_viewer",
            "qa_campaign",
            "retrospect",
            "audit_harness",
        ):
            self.assertIn(name, opt)


if __name__ == "__main__":
    unittest.main()
