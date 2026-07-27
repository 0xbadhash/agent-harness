"""Contract: smoke unit is a script wrapper (no nested bash -c in plugin)."""
from __future__ import annotations

import re
import stat
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "smoke_unit.sh"
PLUGIN = ROOT / ".agents" / "product_plugin.yaml"


class TestSmokeUnitWrapper(unittest.TestCase):
    def test_wrapper_script_exists_and_executable(self):
        self.assertTrue(WRAPPER.is_file(), "scripts/smoke_unit.sh missing")
        mode = WRAPPER.stat().st_mode
        self.assertTrue(mode & stat.S_IXUSR, "smoke_unit.sh must be executable")

    def test_plugin_unit_smoke_uses_wrapper_not_inline_bash_c(self):
        text = PLUGIN.read_text(encoding="utf-8")
        self.assertIn("smoke_unit.sh", text)
        # Forbidden fragile pattern that broke night_shift
        self.assertIsNone(
            re.search(r'cmd:\s*\["bash",\s*"-c"', text),
            "product_plugin smoke must not use bash -c inline",
        )

    def test_wrapper_help_or_dry_runs(self):
        # --list-python prints interpreter path and exits 0 without full suite
        r = subprocess.run(
            ["bash", str(WRAPPER), "--print-python"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertTrue((r.stdout or "").strip(), "expected python path on stdout")


if __name__ == "__main__":
    unittest.main()
