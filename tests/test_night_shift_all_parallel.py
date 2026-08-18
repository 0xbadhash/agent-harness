#!/usr/bin/env python3
"""Parallel night_shift_all: product list size + jobs wiring."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "bin" / "night_shift_all_products.py"
    spec = importlib.util.spec_from_file_location("night_shift_all_products", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestNightShiftAllParallel(unittest.TestCase):
    def test_ten_product_list_unchanged(self):
        mod = _load()
        products = mod._load_products(ROOT / "config" / "night_shift_products.yaml")
        ids = [n for n, _ in products]
        self.assertEqual(len(ids), 10, ids)
        for need in (
            "watchlist",
            "email-detach",
            "substack-push",
            "second-brain",
            "catalyxt",
            "agent-harness",
            "ocr-ledger",
            "zk-business-card",
            "bip39lab",
            "figure-it-out",
        ):
            self.assertIn(need, ids)

    def test_run_one_dry_returns_dict(self):
        mod = _load()
        row = mod.run_one(
            "agent-harness",
            ROOT,
            vault=ROOT / ".agents",
            quick=True,
            skip_live=True,
            dry_run=True,
        )
        self.assertIn("ok", row)
        self.assertEqual(row["name"], "agent-harness")


if __name__ == "__main__":
    unittest.main()
