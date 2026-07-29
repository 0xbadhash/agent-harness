"""start_feature scaffold."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "start_feature.py"


class TestStartFeature(unittest.TestCase):
    def test_writes_pr_draft_with_spec_stub(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            r = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--slug",
                    "demo-feat",
                    "--write-spec-stub",
                    "--title",
                    "Demo",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            pr = (root / "PR_DRAFT.md").read_text(encoding="utf-8")
            self.assertIn("**Spec:**", pr)
            self.assertIn("## Traceability", pr)
            specs = list((root / ".agents" / "specs").glob("*-demo-feat.md"))
            self.assertEqual(len(specs), 1)

    def test_waiver_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            r = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root",
                    str(root),
                    "--slug",
                    "fix",
                    "--waiver",
                    "hotfix",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            pr = (root / "PR_DRAFT.md").read_text(encoding="utf-8")
            self.assertIn("**Spec waiver:** hotfix", pr)


if __name__ == "__main__":
    unittest.main()
