"""Open-web Chromium launch policy. The refused build must not start."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "openweb_chromium_launch.py"
    spec = importlib.util.spec_from_file_location("openweb_chromium_launch", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestOpenwebChromiumLaunch(unittest.TestCase):
    def test_refused_build_does_not_launch(self):
        mod = _load()
        code, argv = mod.plan_launch("Chromium 156.0.8078.4", ["--headless=new"])
        self.assertEqual(code, 2)
        self.assertEqual(argv, [])

    def test_newer_build_launches_without_sandbox_off_or_unconfined(self):
        mod = _load()
        code, argv = mod.plan_launch(
            "Chromium 156.0.8078.79",
            ["--headless=new", "--no-sandbox", "--disable-setuid-sandbox"],
        )
        self.assertEqual(code, 0)
        joined = " ".join(argv)
        self.assertNotIn("--no-sandbox", argv)
        self.assertNotIn("--disable-setuid-sandbox", argv)
        self.assertNotIn("apparmor=unconfined", joined)
        self.assertIn("apparmor=hermes-openweb-chromium", joined)
        self.assertIn("--headless=new", argv)
