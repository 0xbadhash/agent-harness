#!/usr/bin/env python3
"""Parallel night_shift_all: product list size + jobs wiring."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "bin" / "night_shift_all_products.py"
    spec = importlib.util.spec_from_file_location("night_shift_all_products", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestNightVaultGuard(unittest.TestCase):
    def test_unset_defaults_outside_harness(self):
        mod = _load()
        vault, err = mod.resolve_night_vault(Path(""))
        self.assertEqual(err, "")
        self.assertIsNotNone(vault)
        assert vault is not None
        self.assertEqual(vault, Path("/opt/second-brain/vault").resolve())
        self.assertFalse(str(vault).startswith(str(ROOT.resolve())))

    def test_harness_checkout_is_refused(self):
        mod = _load()
        vault, err = mod.resolve_night_vault(ROOT)
        self.assertIsNone(vault)
        self.assertIn("REFUSING", err)
        self.assertIn("harness checkout", err)


class TestStrictVerdictLine(unittest.TestCase):
    def test_dry_run_summary_names_pass_or_fail(self):
        mod = _load()
        when = datetime(2026, 11, 13, tzinfo=timezone.utc)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.write_summary(
                Path("/no/such-vault"),
                when,
                [{"name": "a", "ok": False, "exit": 1, "root": "/x"}],
                True,
            )
        self.assertIn("=== DONE night-shift-all FAIL ===", buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            mod.write_summary(
                Path("/no/such-vault"),
                when,
                [{"name": "a", "ok": True, "exit": 0, "root": "/x"}],
                True,
            )
        self.assertIn("=== DONE night-shift-all PASS ===", buf.getvalue())


class TestNightShiftAllParallel(unittest.TestCase):
    def test_product_list_includes_jasmine(self):
        """Config lists all products (incl jasmine); runtime load filters to existing dirs.

        CI runners typically only have agent-harness checked out under $HOME, so
        _load_products correctly returns a subset. Assert the YAML SoT, not the
        host filesystem inventory.
        """
        mod = _load()
        cfg = ROOT / "config" / "night_shift_products.yaml"
        expected = (
            "watchlist",
            "email-detach",
            "substack-push",
            "second-brain",
            "catalyxt",
            "agent-harness",
            "zk-business-card",
            "bip39lab",
            "figure-it-out",
            "jasmine",
            "ui",
            "mission-feeds",
        )
        cfg_ids: list[str] = []
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            line = line.lstrip("-").strip()
            pid = line.split(":", 1)[0].strip()
            if pid:
                cfg_ids.append(pid)
        self.assertEqual(cfg_ids, list(expected), cfg_ids)
        for need in expected:
            self.assertIn(need, cfg_ids)

        products = mod._load_products(cfg)
        loaded = [n for n, _ in products]
        self.assertTrue(loaded, "expected at least one existing product dir")
        for n in loaded:
            self.assertIn(n, expected)
        self.assertIn("agent-harness", loaded)

    def test_run_one_dry_returns_dict(self):
        mod = _load()
        row = mod.run_one(
            "agent-harness",
            ROOT,
            vault=ROOT / ".agents",
            quick=True,
            skip_live=True,
            dry_run=True,
        )
        self.assertIn("ok", row)
        self.assertEqual(row["name"], "agent-harness")

    def test_default_jobs_is_two_and_timeout_is_env(self):
        """Unset default is 2. The night unit exports NIGHT_SHIFT_JOBS=1, so
        the assertion must not read that ambient value as the code default.
        """
        saved_jobs = os.environ.pop("NIGHT_SHIFT_JOBS", None)
        saved_timeout = os.environ.pop("NIGHT_SHIFT_PRODUCT_TIMEOUT", None)
        try:
            mod = _load()
            self.assertEqual(mod.DEFAULT_JOBS, 2)
            self.assertEqual(mod.PRODUCT_TIMEOUT_S, 7200)
            os.environ["NIGHT_SHIFT_JOBS"] = "1"
            self.assertEqual(_load().DEFAULT_JOBS, 1)
        finally:
            if saved_jobs is None:
                os.environ.pop("NIGHT_SHIFT_JOBS", None)
            else:
                os.environ["NIGHT_SHIFT_JOBS"] = saved_jobs
            if saved_timeout is None:
                os.environ.pop("NIGHT_SHIFT_PRODUCT_TIMEOUT", None)
            else:
                os.environ["NIGHT_SHIFT_PRODUCT_TIMEOUT"] = saved_timeout


if __name__ == "__main__":
    unittest.main()
