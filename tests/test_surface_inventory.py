#!/usr/bin/env python3
"""surface_inventory: known hosts listed; pane default call exits 0."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import surface_inventory as si  # noqa: E402


class TestSurfaceInventory(unittest.TestCase):
    def test_pane_default_call_exits_0(self):
        rc = si.main([])
        self.assertEqual(rc, 0)

    def test_known_hosts_include_ceo_list(self):
        urls = {u for _, u in si.KNOWN_CATALYXT_HOSTS}
        for need in (
            "https://catalyxt.xyz",
            "https://watchlist.catalyxt.xyz",
            "https://artauthenticity.xyz",
            "https://bip39.catalyxt.xyz",
            "https://figure.catalyxt.xyz",
            "https://card.catalyxt.xyz",
            "https://ui.catalyxt.xyz",
        ):
            self.assertIn(need, urls)

    def test_no_typo_host(self):
        joined = " ".join(u for _, u in si.KNOWN_CATALYXT_HOSTS)
        self.assertNotIn("catalyxt.xyzz", joined)
        self.assertNotIn("bip39lab.catalyxt", joined)

    def test_merge_includes_known(self):
        rows = si._merge_targets(ROOT / "config" / "zap_targets.yaml")
        urls = {r["url"].rstrip("/") for r in rows}
        self.assertIn("https://figure.catalyxt.xyz", urls)
        self.assertIn("https://card.catalyxt.xyz", urls)


if __name__ == "__main__":
    unittest.main()
