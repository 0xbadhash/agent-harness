#!/usr/bin/env python3
"""HSQ-3 P3 G15 protect SoT pin."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_protect_sot_pin as pin  # noqa: E402


class TestProtectPin(unittest.TestCase):
    def test_ac_1_identical(self):
        with tempfile.TemporaryDirectory() as td:
            sot = Path(td) / "sot"
            prod = Path(td) / "prod"
            for root in (sot, prod):
                (root / "scripts").mkdir(parents=True)
                (root / "scripts" / "pipeline_state.py").write_text("a=1\n", encoding="utf-8")
                (root / "scripts" / "hard_gates.py").write_text("b=2\n", encoding="utf-8")
            self.assertEqual(pin.check_product(sot, prod), [])

    def test_ac_2_drift(self):
        with tempfile.TemporaryDirectory() as td:
            sot = Path(td) / "sot"
            prod = Path(td) / "prod"
            for root in (sot, prod):
                (root / "scripts").mkdir(parents=True)
            (sot / "scripts" / "pipeline_state.py").write_text("sot\n", encoding="utf-8")
            (prod / "scripts" / "pipeline_state.py").write_text("fork\n", encoding="utf-8")
            (sot / "scripts" / "hard_gates.py").write_text("same\n", encoding="utf-8")
            (prod / "scripts" / "hard_gates.py").write_text("same\n", encoding="utf-8")
            d = pin.check_product(sot, prod)
            self.assertIn("scripts/pipeline_state.py", d)

    def test_ac_3_strict_cli(self):
        with tempfile.TemporaryDirectory() as td:
            sot = Path(td) / "sot"
            prod = Path(td) / "prod"
            for root in (sot, prod):
                (root / "scripts").mkdir(parents=True)
            (sot / "scripts" / "pipeline_state.py").write_text("sot\n", encoding="utf-8")
            (prod / "scripts" / "pipeline_state.py").write_text("fork\n", encoding="utf-8")
            (sot / "scripts" / "hard_gates.py").write_text("x\n", encoding="utf-8")
            (prod / "scripts" / "hard_gates.py").write_text("x\n", encoding="utf-8")
            rc = pin.main(["--sot", str(sot), "--product", str(prod), "--strict"])
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
