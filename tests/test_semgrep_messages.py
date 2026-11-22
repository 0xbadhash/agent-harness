#!/usr/bin/env python3
"""Every Semgrep rule message includes a FIX hint."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestSemgrepMessages(unittest.TestCase):
    def test_every_rule_message_has_fix(self):
        text = (ROOT / ".semgrep.yml").read_text(encoding="utf-8")
        ids = re.findall(r"(?m)^\s*- id:\s*(\S+)", text)
        messages = re.findall(r'(?m)^\s*message:\s*"(.*)"\s*$', text)
        self.assertGreaterEqual(len(ids), 6)
        self.assertEqual(len(messages), len(ids))
        for rule_id, message in zip(ids, messages):
            self.assertIn("FIX:", message, rule_id)


if __name__ == "__main__":
    unittest.main()
