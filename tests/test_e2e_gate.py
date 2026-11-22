"""e2e_gate discovers scenarios, refuses the bad Chromium pin, and writes the gate."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "e2e_gate.py"
    spec = importlib.util.spec_from_file_location("e2e_gate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestE2EGate(unittest.TestCase):
    def test_refused_build_does_not_run_scenarios(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "tests" / "e2e"
            spec.mkdir(parents=True)
            (spec / "home.spec.ts").write_text("test('home', () => {})\n", encoding="utf-8")
            report = root / "E2E_GATE.md"
            code = mod.run_gate(root, report, version="156.0.8078.4", runner=["false"])
            self.assertEqual(code, 2)
            text = report.read_text(encoding="utf-8")
            self.assertIn("E2E-GATE", text)
            self.assertIn("status: FAIL", text)
            self.assertIn("156.0.8078.4", text)

    def test_missing_scenarios_fail(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "E2E_GATE.md"
            code = mod.run_gate(root, report, version="156.0.8078.79", runner=["true"])
            self.assertEqual(code, 1)
            self.assertIn("no Playwright scenarios", report.read_text(encoding="utf-8"))

    def test_runner_exit_codes(self):
        mod = _load()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = root / "e2e"
            spec.mkdir()
            (spec / "a.spec.ts").write_text("test\n", encoding="utf-8")
            report = root / "E2E_GATE.md"
            self.assertEqual(
                mod.run_gate(root, report, version="156.0.8078.79", runner=["true"]),
                0,
            )
            self.assertIn("status: PASS", report.read_text(encoding="utf-8"))
            self.assertIn("a.spec.ts", report.read_text(encoding="utf-8"))
            self.assertEqual(
                mod.run_gate(root, report, version="156.0.8078.79", runner=["false"]),
                1,
            )
            self.assertIn("status: FAIL", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
