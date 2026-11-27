"""Lint configuration pins the categorical bans (T2087U item 4)."""
from __future__ import annotations

import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class TestRuffConfig(unittest.TestCase):
    def setUp(self):
        self.cfg = tomllib.loads((ROOT / "ruff.toml").read_text(encoding="utf-8"))

    def test_categorical_families_selected(self):
        select = set(self.cfg["lint"]["select"])
        for rule in ("B", "BLE", "S602", "C90"):
            self.assertIn(rule, select)

    def test_complexity_threshold(self):
        self.assertEqual(self.cfg["lint"]["mccabe"]["max-complexity"], 20)

    def test_classic_rules_stay(self):
        select = set(self.cfg["lint"]["select"])
        for rule in ("E", "F", "W"):
            self.assertIn(rule, select)


if __name__ == "__main__":
    unittest.main()
