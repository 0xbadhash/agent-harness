"""portfolio_install_report."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import portfolio_install_report as pir  # noqa: E402


class TestPortfolio(unittest.TestCase):
    def test_lagging(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            p = t / "prod"
            (p / ".agents").mkdir(parents=True)
            (p / ".agents" / "HARNESS_VERSION").write_text("0.0.1\n", encoding="utf-8")
            rows = pir.evaluate([("prod", p)], "1.4.11")
            self.assertTrue(rows[0].lagging)
            out = t / "r.md"
            pir.write_report(rows, "1.4.11", out)
            self.assertIn("Lagging", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
