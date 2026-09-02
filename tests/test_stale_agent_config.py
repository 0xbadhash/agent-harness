#!/usr/bin/env python3
"""Stale agent-config refs fail closed."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_stale_agent_config as sac  # noqa: E402


class TestStaleAgentConfig(unittest.TestCase):
    def test_harness_sot_resolves(self):
        ok, msgs = sac.check(ROOT)
        self.assertTrue(ok, msgs)

    def test_missing_script_in_agents_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            (td / "scripts").mkdir()
            (td / "scripts" / "next_skill.py").write_text("# x\n", encoding="utf-8")
            (td / "AGENTS.md").write_text(
                "Run `python3 scripts/does_not_exist_zz.py`\n", encoding="utf-8"
            )
            ok, msgs = sac.check(td)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("does_not_exist_zz.py" in m for m in msgs), msgs)

    def test_ship_skill_missing_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            (td / "scripts").mkdir()
            (td / "scripts" / "next_skill.py").write_text("# x\n", encoding="utf-8")
            (td / "config").mkdir()
            (td / "config" / "ship_skills.txt").write_text("not_a_real_skill\n", encoding="utf-8")
            ok, msgs = sac.check(td)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("not_a_real_skill" in m for m in msgs), msgs)


if __name__ == "__main__":
    unittest.main()
