"""Vault write helpers: group-friendly write + clear EACCES remediation."""
from __future__ import annotations

import stat
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vault_fs  # noqa: E402


class TestVaultFs(unittest.TestCase):
    def test_write_text_creates_group_writable_when_possible(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "proj" / "night-shift-log.md"
            vault_fs.write_text(p, "# hi\n")
            self.assertTrue(p.is_file())
            self.assertEqual(p.read_text(encoding="utf-8"), "# hi\n")
            mode = p.stat().st_mode
            # Prefer group-writable for shared vaults (best-effort)
            self.assertTrue(mode & stat.S_IWUSR)

    def test_is_writable_false_for_missing_parent_readonly_sim(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "nope" / "x.md"
            # parent missing → not yet writable until mkdir
            self.assertFalse(vault_fs.path_is_writable(p))

    def test_remediation_mentions_ensure_script(self):
        msg = vault_fs.remediation_hint(Path("/opt/second-brain/vault/01-Projects/x/log.md"))
        self.assertIn("ensure_vault_group_write", msg)
        self.assertIn("secondbrain", msg.lower())

    def test_ensure_script_check_mode_exit(self):
        # --check on a temp writable tree exits 0
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            proj = root / "01-Projects" / "demo"
            proj.mkdir(parents=True)
            (proj / "night-shift-log.md").write_text("x\n", encoding="utf-8")
            r = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "ensure_vault_group_write.py"),
                    "--vault",
                    str(root),
                    "--check",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
