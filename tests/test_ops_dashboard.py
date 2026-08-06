"""ops_dashboard generator."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ops_dashboard as od  # noqa: E402


class TestOpsDashboard(unittest.TestCase):
    def test_render_green_minimal(self):
        d = od.Dashboard(
            when_utc="t",
            when_hkt="t",
            overall="GREEN",
            went_well=[od.Item("green", "x", "ok")],
        )
        md = od.render(d, None)
        self.assertIn("OPS DASHBOARD", md)
        self.assertIn("GREEN", md)

    def test_build_runs(self):
        d = od.build(None, quick=True)
        self.assertIn(d.overall, ("GREEN", "ATTENTION", "RED"))
        md = od.render(d, None)
        self.assertIn("What went well", md)


if __name__ == "__main__":
    unittest.main()
