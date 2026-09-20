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
    def test_product_list_includes_jasmine(self):
        """Config lists all products (incl jasmine); runtime load filters to existing dirs.

        CI runners typically only have agent-harness checked out under $HOME, so
        _load_products correctly returns a subset. Assert the YAML SoT, not the
        host filesystem inventory.
        """
        mod = _load()
        cfg = ROOT / "config" / "night_shift_products.yaml"
        expected = (
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
            "jasmine",
        )
        cfg_ids: list[str] = []
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            line = line.lstrip("-").strip()
            pid = line.split(":", 1)[0].strip()
            if pid:
                cfg_ids.append(pid)
        self.assertEqual(len(cfg_ids), 11, cfg_ids)
        for need in expected:
            self.assertIn(need, cfg_ids)

        products = mod._load_products(cfg)
        loaded = [n for n, _ in products]
        self.assertTrue(loaded, "expected at least one existing product dir")
        for n in loaded:
            self.assertIn(n, expected)
        self.assertIn("agent-harness", loaded)

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
