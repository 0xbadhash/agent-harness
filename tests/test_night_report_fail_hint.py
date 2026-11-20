#!/usr/bin/env python3
"""Failed-gate names and one-line fixes in the all-product night report."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str, name: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestNightReportFailHint(unittest.TestCase):
    def test_two_gates_fix_order_summary_and_promote(self):
        readiness = _load("scripts/night_shift_readiness.py", "ns_readiness_fail_hint")
        orchestrator = _load("bin/night_shift_all_products.py", "ns_all_fail_hint")
        sys.path.insert(0, str(ROOT / "scripts"))
        import promote_night_fails as pnf  # noqa: E402

        long_tail = "❌ scripts/x.py:3 [absolute_user_path] " + ("A" * 160)
        results = [
            {
                "name": "hardcodes",
                "ok": False,
                "exit": 1,
                "stderr_tail": long_tail,
            },
            {
                "name": "validate_full",
                "ok": False,
                "exit": 2,
                "stderr_tail": "validate_full failed on type check",
            },
            {"name": "product_smoke", "ok": True, "exit": 0},
        ]
        recs = readiness.recommendations_from(results, [], "demo", root=ROOT)
        when = datetime(2026, 11, 20, tzinfo=timezone.utc)
        report = readiness.build_report_md(
            when=when,
            results=results,
            recs=recs,
            mode="full",
            product_id="demo",
        )
        fix_lines = [ln for ln in report.splitlines() if ln.startswith("Fix:")]
        self.assertEqual(len(fix_lines), 2)
        self.assertIn("Hardcode scan failed", fix_lines[0])
        self.assertIn("validate.py full", fix_lines[1])
        self.assertLess(report.index("### hardcodes"), report.index("### validate_full"))
        self.assertEqual(
            pnf.FAIL_GATE.findall(report),
            ["hardcodes", "validate_full"],
        )

        hints = orchestrator.parse_fail_hints(report)
        self.assertEqual([h["gate"] for h in hints], ["hardcodes", "validate_full"])
        self.assertEqual(hints[0]["exit"], "1")
        self.assertEqual(hints[1]["exit"], "2")
        self.assertEqual(len(hints[0]["first"]), 120)
        self.assertTrue(hints[0]["first"].startswith("❌ scripts/x.py:3"))

        row = {
            "name": "demo",
            "ok": False,
            "exit": 1,
            "root": "/x",
            "tail": "raw tail stays",
            "fail_hints": hints,
        }
        attached = orchestrator.attach_fail_hints(dict(row), report)
        self.assertEqual(attached["exit"], 1)
        self.assertEqual(row["exit"], 1)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            orchestrator.write_summary(
                Path("/no/such-vault"),
                when,
                [row],
                True,
            )
        text = buf.getvalue()
        self.assertIn("=== DONE night-shift-all FAIL ===", text)
        self.assertLess(
            text.index("- gate `hardcodes`"),
            text.index("- gate `validate_full`"),
        )
        boxes = [
            ln
            for ln in text.splitlines()
            if ln.startswith("- [ ] **demo** gate `")
        ]
        self.assertEqual(len(boxes), 2)
        self.assertIn("gate `hardcodes`", boxes[0])
        self.assertIn("gate `validate_full`", boxes[1])
        self.assertLess(text.index(boxes[0]), text.index(boxes[1]))
        self.assertNotIn("/opt/second-brain/vault", text)


if __name__ == "__main__":
    unittest.main()
