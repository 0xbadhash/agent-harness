"""--root must stamp the product tree, not the harness repo that holds this script."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
SCRIPT = HARNESS / "scripts" / "sync_docs_full.py"
# Files the import-time paths used to stamp even when --root pointed elsewhere.
HARNESS_DOCS = (
    HARNESS / "README.md",
    HARNESS / "docs" / "PRODUCT.md",
    HARNESS / "WORKFLOW_DOCUMENTATION.md",
)
PRODUCT_VERSION = "v0.5.3"


class TestRootStaysInsideProduct(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.product = self.tmp / "product"
        self.product.mkdir()
        (self.product / "README.md").write_text("# Widget\n", encoding="utf-8")
        git = ["git", "-C", str(self.product)]
        subprocess.run(["git", "init", "-q", str(self.product)], check=True)
        subprocess.run([*git, "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run([*git, "config", "user.name", "t"], check=True)
        subprocess.run([*git, "add", "README.md"], check=True)
        subprocess.run([*git, "commit", "-qm", "init"], check=True)
        subprocess.run([*git, "tag", PRODUCT_VERSION], check=True)
        self.before = {path: path.read_bytes() for path in HARNESS_DOCS if path.is_file()}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_root_flag_stamps_product_readme_and_leaves_harness_untouched(self):
        env = {k: v for k, v in os.environ.items() if k not in {"PRODUCT_ROOT", "PRODUCT_VAULT_ROOT"}}
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.product), "--skip-vault"],
            cwd=self.tmp,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for path, blob in self.before.items():
            self.assertEqual(path.read_bytes(), blob, f"{path} changed")
        product_readme = (self.product / "README.md").read_text(encoding="utf-8")
        self.assertIn(PRODUCT_VERSION, product_readme)
        self.assertIn("CURRENT_RELEASE", product_readme)
