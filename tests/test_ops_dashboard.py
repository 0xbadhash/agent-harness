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

    def test_render_embeds_watchlist_and_scout(self):
        d = od.Dashboard(
            when_utc="t",
            when_hkt="t",
            overall="GREEN",
            went_well=[od.Item("green", "x", "ok")],
        )
        md = od.render(d, None)
        self.assertIn("## Desk board", md)
        self.assertIn("## Watchlist notes", md)
        self.assertIn("![[agent-tasks/WATCHLIST-NOTES]]", md)
        self.assertIn("## Scout", md)
        self.assertIn("![[agent-tasks/SCOUT]]", md)
        self.assertIn("## Substack", md)
        self.assertIn("![[agent-tasks/SUBSTACK]]", md)
        self.assertLess(md.find("## Desk board"), md.find("## Watchlist notes"))
        self.assertLess(md.find("## Watchlist notes"), md.find("## Scout"))
        self.assertLess(md.find("## Scout"), md.find("## Substack"))
        self.assertLess(md.find("## Substack"), md.find("## At a glance"))
        scout_i = md.find("## Scout")
        sub_i = md.find("## Substack")
        glance_i = md.find("## At a glance")
        self.assertIn("![[agent-tasks/SUBSTACK]]", md[sub_i:glance_i])
        self.assertIn("![[agent-tasks/SCOUT]]", md[scout_i:sub_i])


if __name__ == "__main__":
    unittest.main()
