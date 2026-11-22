"""promote_night_fails."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import promote_night_fails as pnf  # noqa: E402


class TestPromote(unittest.TestCase):
    def test_repeated_gate(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            for name in ("a", "b"):
                art = t / name / ".agents" / "artifacts"
                art.mkdir(parents=True)
                (art / "NIGHT_SHIFT_REPORT.md").write_text(
                    "| `hardcodes` | ❌ |\n| `validate_full` | ✅ |\n",
                    encoding="utf-8",
                )
            promos = pnf.evaluate(
                [("a", t / "a"), ("b", t / "b")], min_count=2
            )
            gates = {p.gate for p in promos}
            self.assertIn("hardcodes", gates)

    def test_write_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "p.md"
            pnf.write_artifact(
                [pnf.Promotion("hardcodes", 2, ["a", "b"], "fix")], out
            )
            self.assertIn("hardcodes", out.read_text(encoding="utf-8"))

    def test_report_only_tickets_names_gate_and_skips_stubs(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            out = t / "NIGHT_FAIL_TICKETS.md"
            pnf.write_report_only_tickets(
                [
                    (
                        "demo",
                        "hardcodes",
                        "Hardcode scan failed — remove secrets/absolute paths.",
                    )
                ],
                out,
            )
            text = out.read_text(encoding="utf-8")
            self.assertIn("report-only; autofix not run", text)
            self.assertIn("gate `hardcodes`", text)
            self.assertIn(
                "Hardcode scan failed — remove secrets/absolute paths.",
                text,
            )
            self.assertNotIn("assertTrue", text)
            self.assertEqual(list(t.glob("test_gate_*.py")), [])
            self.assertFalse((t / "tests" / "night_fail_promotions").exists())


if __name__ == "__main__":
    unittest.main()
