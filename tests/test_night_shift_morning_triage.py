"""Morning triage after night_shift."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import night_shift_morning_triage as mt  # noqa: E402


def _product(td: Path, name: str, overall: str) -> Path:
    root = td / name
    art = root / ".agents" / "artifacts"
    art.mkdir(parents=True)
    (art / "NIGHT_SHIFT_TODO.md").write_text(
        f"# TODO\n\n**Overall:** **{overall}**\n\n"
        + ("| `hardcodes` | ❌ |\n" if overall == "FAIL" else "| `hardcodes` | ✅ |\n"),
        encoding="utf-8",
    )
    return root


class TestMorningTriage(unittest.TestCase):
    def test_all_pass_exit_via_evaluate(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            a = _product(t, "a", "PASS")
            b = _product(t, "b", "PASS")
            res = mt.evaluate([("a", a), ("b", b)], recheck=False)
            self.assertTrue(all(r.overall == "PASS" for r in res))
            out = t / "MORNING_TRIAGE.md"
            mt.write_artifact(res, out)
            text = out.read_text(encoding="utf-8")
            self.assertIn("**Overall:** PASS", text)
            self.assertIn("MORNING_TRIAGE", text)

    def test_fail_detected(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            a = _product(t, "a", "FAIL")
            res = mt.evaluate([("a", a)], recheck=False)
            self.assertEqual(res[0].overall, "FAIL")
            self.assertIn("hardcodes", res[0].fail_gates)

    def test_recheck_can_clear(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            a = _product(t, "a", "FAIL")
            with mock.patch.object(mt, "_recheck", return_value=True):
                res = mt.evaluate([("a", a)], recheck=True)
            self.assertEqual(res[0].overall, "PASS")
            self.assertTrue(res[0].rechecked)

    def test_cli_all_pass(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            a = _product(t, "a", "PASS")
            out = t / "out.md"
            rc = mt.main(["--root", str(a), "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
