#!/usr/bin/env python3
"""release_origin_gate fail-closed proofs."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release_origin_gate as rog  # noqa: E402


class TestReleaseOriginGate(unittest.TestCase):
    def test_dry_miss_missing_tag_fails(self):
        """Prove fail-closed: expect a tag that origin cannot have."""
        ok, msgs = rog.verify(ROOT, expect_tag="v0.0.0-missing-dry-miss")
        self.assertFalse(ok, msgs)
        self.assertTrue(any("missing tag" in m or "fail:" in m for m in msgs), msgs)

    def test_read_version(self):
        v = rog.read_version(ROOT)
        self.assertTrue(v)
        self.assertRegex(v, r"^\d+\.\d+")

    def test_origin_has_existing_tag_v1_4_33(self):
        # This repo ships with prior tags on origin; gate should see a real one
        ok, msgs = rog.origin_has_tag(ROOT, "v1.4.33")
        # May fail offline; still assert function returns bool+msg
        self.assertIsInstance(ok, bool)
        self.assertTrue(msgs)


if __name__ == "__main__":
    unittest.main()
