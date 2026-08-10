#!/usr/bin/env python3
"""HSQ-3 P2 gates unit tests."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_security_paths as sp  # noqa: E402
import check_spec_hash as sh  # noqa: E402
import check_threat_tags as tt  # noqa: E402
import check_waiver_budget as wb  # noqa: E402


class TestSpecHash(unittest.TestCase):
    def test_ac_1_missing_spec(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text("**Spec:** .agents/specs/nope.md\n", encoding="utf-8")
            ok, _ = sh.check(root, root / "PR_DRAFT.md")
            self.assertFalse(ok)

    def test_ac_2_wrong_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec = root / ".agents" / "specs" / "s.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("AC-1 x\n", encoding="utf-8")
            bad = "0" * 64
            (root / "PR_DRAFT.md").write_text(
                f"**Spec:** .agents/specs/s.md\n**spec_sha256:** {bad}\n",
                encoding="utf-8",
            )
            ok, msgs = sh.check(root, root / "PR_DRAFT.md")
            self.assertFalse(ok)

    def test_ac_3_match(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spec = root / ".agents" / "specs" / "s.md"
            spec.parent.mkdir(parents=True)
            body = "AC-1 x\n"
            spec.write_text(body, encoding="utf-8")
            digest = hashlib.sha256(body.encode()).hexdigest()
            (root / "PR_DRAFT.md").write_text(
                f"**Spec:** .agents/specs/s.md\n**spec_sha256:** {digest}\n",
                encoding="utf-8",
            )
            ok, msgs = sh.check(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)


class TestThreatTags(unittest.TestCase):
    def test_ac_4_needs_tags(self):
        ok, _ = tt.check("## Threat notes\n- something vague\n", runtime=True)
        self.assertFalse(ok)

    def test_tags_ok(self):
        ok, msgs = tt.check(
            "## Threat notes\n- authz boundary\n- secrets in env\n",
            runtime=True,
        )
        self.assertTrue(ok, msgs)


class TestSecurityPaths(unittest.TestCase):
    def test_ac_6_no_config(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ok, msgs = sp.check(root, "A", "B")
            self.assertTrue(ok)


class TestWaiverBudget(unittest.TestCase):
    def test_feature_skips(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text("**Spec:** x.md\n", encoding="utf-8")
            ok, _ = wb.check(root, root / "PR_DRAFT.md")
            self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
