"""B1 spec_gate."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import spec_gate as sg  # noqa: E402


class TestSpecGate(unittest.TestCase):
    def test_waiver_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text("**Spec waiver:** chore\n", encoding="utf-8")
            ok, _ = sg.check(root)
            self.assertTrue(ok)

    def test_missing_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text("no spec\n", encoding="utf-8")
            ok, msgs = sg.check(root)
            self.assertFalse(ok)

    def test_spec_file_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec = root / ".agents" / "specs" / "x.md"
            spec.parent.mkdir(parents=True)
            spec.write_text(
                "# s\n\n## Grill-me\n\n**Status:** complete\n\n"
                "### G1\n- Q: Outcome?\n  - A: Done.\n"
                "### G2\n- Q: Non-goal?\n  - A: Nothing extra.\n"
                "### G3\n- Q: Product?\n  - A: This repo.\n",
                encoding="utf-8",
            )
            (root / "PR_DRAFT.md").write_text(
                "**Spec:** .agents/specs/x.md\n", encoding="utf-8"
            )
            ok, msgs = sg.check(root)
            self.assertTrue(ok, msgs)

    def test_pipeline_waiver(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            st = root / ".agents" / "state"
            st.mkdir(parents=True)
            (st / "pipeline.json").write_text(
                json.dumps({"phase": "init", "waiver": "hotfix"}),
                encoding="utf-8",
            )
            ok, _ = sg.check(root, allow_missing_draft=True)
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
