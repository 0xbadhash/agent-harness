#!/usr/bin/env python3
"""CI matrix steps 1–5 unit checks."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_property_tests as pt  # noqa: E402


class TestStep2SkipHardGates(unittest.TestCase):
    def test_skip_requires_env(self):
        env = os.environ.copy()
        env.pop("ALLOW_SKIP_HARD_GATES", None)
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "pr_validator.py"), "--skip-hard-gates"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ALLOW_SKIP_HARD_GATES", (r.stderr or "") + (r.stdout or ""))


class TestStep5PropertyTests(unittest.TestCase):
    def test_disabled_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(pt, "_load_modules", return_value=(False, [])):
                ok, msgs = pt.check(root)
            self.assertTrue(ok)

    def test_enabled_missing_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "tests").mkdir()
            (root / "tests" / "test_empty.py").write_text(
                "def test_x():\n    assert True\n", encoding="utf-8"
            )
            with mock.patch.object(
                pt, "_load_modules", return_value=(True, ["my_parser/core"])
            ):
                ok, msgs = pt.check(root)
            self.assertFalse(ok)


class TestDocsAndTemplates(unittest.TestCase):
    def test_ci_matrix_doc(self):
        p = ROOT / "docs" / "ci-matrix.md"
        self.assertTrue(p.is_file())
        text = p.read_text(encoding="utf-8")
        self.assertIn("J12 Semgrep", text)
        self.assertIn("J13 ZAP", text)

    def test_daytime_template_fail_closed(self):
        t = (ROOT / "templates" / "daytime-gates.yml").read_text(encoding="utf-8")
        self.assertIn("J3 hardcodes", t)
        self.assertIn("J7 secrets", t)
        self.assertIn("set -euo pipefail", t)

    def test_semgrep_config(self):
        self.assertTrue((ROOT / ".semgrep.yml").is_file())

    def test_zap_targets(self):
        t = (ROOT / "config" / "zap_targets.yaml").read_text(encoding="utf-8")
        self.assertIn("catalyxt", t)
        self.assertIn("watchlist", t)
        self.assertIn("bip39", t)


if __name__ == "__main__":
    unittest.main()
