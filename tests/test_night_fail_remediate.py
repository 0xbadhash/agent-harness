"""night_fail_remediate."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import night_fail_remediate as nfr  # noqa: E402


class TestNightFailRemediate(unittest.TestCase):
    def test_write_tickets(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            out = t / "t.md"
            nfr.write_tickets(
                [
                    nfr.RemediateResult(
                        "watchlist",
                        t / "w",
                        "FAIL",
                        "FAIL",
                        attempts=["ruff"],
                        open_tickets=["[watchlist] fix gate hardcodes"],
                    )
                ],
                out,
            )
            text = out.read_text(encoding="utf-8")
            self.assertIn("NIGHT_FAIL_TICKETS", text)
            self.assertIn("watchlist", text)

    def test_status_pass(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            art = t / ".agents" / "artifacts"
            art.mkdir(parents=True)
            (art / "NIGHT_SHIFT_TODO.md").write_text(
                "Overall: **PASS**.\n", encoding="utf-8"
            )
            o, g = nfr._status(t)
            self.assertEqual(o, "PASS")


if __name__ == "__main__":
    unittest.main()
