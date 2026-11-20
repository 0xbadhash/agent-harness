#!/usr/bin/env python3
"""Literal sys.path / other-product-root boundary checks."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_import_boundaries.py"


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


class TestImportBoundaries(unittest.TestCase):
    def test_literal_outside_repo_fails_with_fix(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "bad.py").write_text(
                'import sys\nsys.path.insert(0, "/opt/other/product")\n',
                encoding="utf-8",
            )
            result = _run(repo)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("[import_boundary]", result.stdout)
            self.assertIn("FIX:", result.stdout)

    def test_literal_scripts_dir_inside_repo_passes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            scripts = repo / "scripts"
            scripts.mkdir()
            (repo / "ok.py").write_text(
                f'import sys\nsys.path.insert(0, "{scripts}")\n',
                encoding="utf-8",
            )
            result = _run(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("import boundary ok", result.stdout)

    def test_import_os_passes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "mod.py").write_text("import os\n", encoding="utf-8")
            result = _run(repo)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("import boundary ok", result.stdout)

    def test_vault_resolve_import_failure_uses_plugin_default(self):
        path = ROOT / "scripts" / "night_shift_readiness.py"
        spec = importlib.util.spec_from_file_location("ns_ready_vault_fb", path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fake = types.ModuleType("vault_resolve")
        saved = sys.modules.get("vault_resolve")
        sys.modules["vault_resolve"] = fake
        env = os.environ.pop("PRODUCT_VAULT_ROOT", None)
        try:
            plugin = {"vault": {"default_root": "/tmp/t2058u-plugin-default"}}
            got = mod._vault_root(plugin, None)
            self.assertEqual(got, Path("/tmp/t2058u-plugin-default"))
        finally:
            if saved is None:
                sys.modules.pop("vault_resolve", None)
            else:
                sys.modules["vault_resolve"] = saved
            if env is not None:
                os.environ["PRODUCT_VAULT_ROOT"] = env


if __name__ == "__main__":
    unittest.main()
