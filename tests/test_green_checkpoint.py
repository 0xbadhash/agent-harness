#!/usr/bin/env python3
"""Green checkpoint stops extra next_skill loops at the same SHA."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import green_checkpoint as gc  # noqa: E402
import next_skill as ns  # noqa: E402


class TestGreenCheckpoint(unittest.TestCase):
    def test_write_and_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            with mock.patch.object(gc, "_sha", return_value="abc" * 8):
                gc.write(td, score=100, sha="abc" * 8)
                ok, msg = gc.head_is_green(td)
            self.assertTrue(ok, msg)
            data = json.loads((td / ".agents" / "state" / "green_checkpoint.json").read_text())
            self.assertEqual(data["score"], 100)

    def test_next_skill_skips_extra_review_when_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            gc.write(td, score=100, sha="deadbeef" * 5)
            with mock.patch.object(gc, "_sha", return_value="deadbeef" * 5):
                nxt, meta = ns.decide(
                    "code_review", base="HEAD~1", head="HEAD", repo=td
                )
            self.assertEqual(nxt, "/release_mgmt")
            self.assertIn("green", meta.get("reason", "").lower())

    def test_next_skill_no_checkpoint_keeps_code_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            (td / ".git").mkdir()
            nxt, meta = ns.decide(
                "execute_dev", base="HEAD~1", head="HEAD", repo=td
            )
            # no git baseline → may skip or code_review; must not be release solely from green
            self.assertNotEqual(nxt, "/release_mgmt")


if __name__ == "__main__":
    unittest.main()
