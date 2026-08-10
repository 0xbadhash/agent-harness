#!/usr/bin/env python3
"""HSQ-2: CODE-REVIEW quality floor + skip log."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hard_gates import _code_review_quality, evaluate  # noqa: E402


class TestCodeReviewQuality(unittest.TestCase):
    def test_auto_stub_fails(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "CODE_REVIEW.md"
            p.write_text(
                "# CODE-REVIEW\n\n**Marker:** CODE-REVIEW\n\n"
                "_Auto-written by run_ship_chain.py at x_\n\np0=0\n",
                encoding="utf-8",
            )
            ok, detail = _code_review_quality(p)
            self.assertFalse(ok)
            self.assertIn("auto-marker", detail)

    def test_good_review_passes(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "CODE_REVIEW.md"
            body = (
                "# CODE-REVIEW\n\n**Marker:** CODE-REVIEW\n\n"
                "## Findings\n"
                "- No P0 issues in scope.\n"
                "- Threshold overrides covered by unit tests.\n\n"
                "## Verdict\nApprove for merge after tests green.\n"
            )
            # pad
            body = body + ("notes " * 20)
            p.write_text(body, encoding="utf-8")
            ok, detail = _code_review_quality(p)
            self.assertTrue(ok, detail)


if __name__ == "__main__":
    unittest.main()
