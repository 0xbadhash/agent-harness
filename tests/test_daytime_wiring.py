"""A3 — check_daytime_wiring + deploy unit presence."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_daytime_wiring as cdw  # noqa: E402


class TestDaytimeWiring(unittest.TestCase):
    def test_harness_tree_ok(self):
        r = cdw.evaluate(ROOT, products=None)
        self.assertTrue(r.ok, r.missing)
        self.assertEqual(r.missing, [])

    def test_fixture_missing_workflow(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "deploy").mkdir()
            (root / "deploy" / "daytime-gates.service").write_text("[Unit]\n", encoding="utf-8")
            (root / "deploy" / "daytime-gates.timer").write_text("[Timer]\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "daytime_readiness_subset.py").write_text("#x\n", encoding="utf-8")
            r = cdw.evaluate(root, products=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("daytime-gates.yml" in m for m in r.missing))

    def test_product_template_optional(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # minimal harness pieces so only product fails when required
            for rel in (
                ".github/workflows/daytime-gates.yml",
                "deploy/daytime-gates.service",
                "deploy/daytime-gates.timer",
                "scripts/daytime_readiness_subset.py",
                "templates/daytime-gates.yml",
            ):
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("x\n", encoding="utf-8")
            prod = root / "fake-product"
            prod.mkdir()
            r = cdw.evaluate(root, products=[prod], require_product_workflow=True)
            self.assertFalse(r.ok)
            self.assertTrue(any("fake-product" in m for m in r.missing))

    def test_cli_exits_zero_on_harness(self):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_daytime_wiring.py"), "--root", str(ROOT)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
