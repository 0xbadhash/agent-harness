#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_agent_config_evals as ev  # noqa: E402


class TestAgentConfigEvals(unittest.TestCase):
    def test_harness_evals_pass(self):
        ok, msgs = ev.run_evals(ROOT)
        self.assertTrue(ok, msgs)


if __name__ == "__main__":
    unittest.main()
