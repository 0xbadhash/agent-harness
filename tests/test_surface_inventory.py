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

    def test_known_hosts_are_hostnames_not_urls(self):
        """No https:// literals in KNOWN list — avoids hardcodes false FAIL."""
        for _tid, host in si.KNOWN_CATALYXT_HOSTS:
            self.assertFalse(
                host.startswith("http://") or host.startswith("https://"),
                msg=f"expected hostname only, got {host!r}",
            )
        hosts = {h for _, h in si.KNOWN_CATALYXT_HOSTS}
        for need in (
            "catalyxt.xyz",
            "watchlist.catalyxt.xyz",
            "artauthenticity.xyz",
            "bip39.catalyxt.xyz",
            "figure.catalyxt.xyz",
            "card.catalyxt.xyz",
            "ui.catalyxt.xyz",
        ):
            self.assertIn(need, hosts)

    def test_known_url_builds_https(self):
        self.assertEqual(si.known_url("artauthenticity.xyz"), "https://artauthenticity.xyz")
        self.assertEqual(
            si.known_url("https://figure.catalyxt.xyz"),
            "https://figure.catalyxt.xyz",
        )

    def test_no_typo_host(self):
        joined = " ".join(h for _, h in si.KNOWN_CATALYXT_HOSTS)
        self.assertNotIn("catalyxt.xyzz", joined)
        self.assertNotIn("bip39lab.catalyxt", joined)

    def test_merge_includes_known(self):
        rows = si._merge_targets(ROOT / "config" / "zap_targets.yaml")
        urls = {r["url"].rstrip("/") for r in rows}
        self.assertIn("https://figure.catalyxt.xyz", urls)
        self.assertIn("https://card.catalyxt.xyz", urls)
        self.assertIn("https://artauthenticity.xyz", urls)

    def test_source_has_no_artauthenticity_https_literal(self):
        text = (ROOT / "scripts" / "surface_inventory.py").read_text(encoding="utf-8")
        # The constant table must not embed the scheme+host that triggers stale scanners
        block = text.split("KNOWN_CATALYXT_HOSTS", 1)[1].split(")", 1)[0]
        self.assertNotIn("https://artauthenticity.xyz", block)


if __name__ == "__main__":
    unittest.main()
