"""Ratchet check() shared by the CLI and hard_gates (T2087U item 1)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_lint_ratchet as clr  # noqa: E402


def _baseline(root: Path, counts: dict[str, int]) -> None:
    p = root / "config" / "lint_ratchet_baseline.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(counts), encoding="utf-8")


class TestRatchetCheck(unittest.TestCase):
    def test_regression_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _baseline(root, {"E501": 1})
            with mock.patch.object(clr, "run_ruff", return_value=[{"code": "E501"}] * 2):
                ok, msgs = clr.check(root)
            self.assertFalse(ok)
            self.assertTrue(any("E501" in m for m in msgs))

    def test_at_baseline_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _baseline(root, {"E501": 1})
            with mock.patch.object(clr, "run_ruff", return_value=[{"code": "E501"}]):
                ok, msgs = clr.check(root)
            self.assertTrue(ok, msgs)

    def test_below_baseline_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _baseline(root, {"E501": 2})
            with mock.patch.object(clr, "run_ruff", return_value=[]):
                ok, msgs = clr.check(root)
            self.assertTrue(ok, msgs)

    def test_unavailable_ruff_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(clr, "run_ruff", side_effect=RuntimeError("no ruff")):
                ok, msgs = clr.check(root)
            self.assertFalse(ok)
            self.assertTrue(any("unavailable" in m.lower() for m in msgs))


if __name__ == "__main__":
    unittest.main()
