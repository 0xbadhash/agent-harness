"""Hardcode scanner skips content/vendored/secrets trees (night_shift P0)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_hardcodes.py"


class TestHardcodeSkips(unittest.TestCase):
    def test_content_urls_not_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "content" / "news").mkdir(parents=True)
            (root / "content" / "news" / "x.json").write_text(
                '{"url": "https://arxiv.org/list/cs.AI/recent"}\n',
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src" / "ok.py").write_text("x = 1\n", encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("no hardcodes", r.stdout)

    def test_secrets_storage_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "secrets").mkdir()
            (root / "secrets" / "storage.json").write_text(
                '{"u": "https://substack.com/foo"}\n',
                encoding="utf-8",
            )
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_real_src_url_still_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "src").mkdir()
            (root / "src" / "bad.py").write_text(
                'API = "https://evil-not-allowlisted.example.org/x"\n',
                encoding="utf-8",
            )
            r = subprocess.run(
                [sys.executable, str(SCRIPT), "--root", str(root)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            # example.org is not on allowlist → fail
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("external_url", r.stdout)


if __name__ == "__main__":
    unittest.main()
