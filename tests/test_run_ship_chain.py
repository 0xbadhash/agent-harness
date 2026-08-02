"""run_ship_chain helpers."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_ship_chain as rsc  # noqa: E402


class TestRunShipChain(unittest.TestCase):
    def test_ensure_pr_draft(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            rsc._ensure_pr_draft(t)
            text = (t / "PR_DRAFT.md").read_text(encoding="utf-8")
            self.assertIn("Evidence pack", text)
            rsc._ensure_artifact(
                t / ".agents" / "artifacts" / "CODE_REVIEW.md",
                "CODE-REVIEW",
                "CODE-REVIEW",
                "p0=0",
            )
            self.assertIn(
                "CODE-REVIEW",
                (t / ".agents" / "artifacts" / "CODE_REVIEW.md").read_text(
                    encoding="utf-8"
                ),
            )


if __name__ == "__main__":
    unittest.main()
