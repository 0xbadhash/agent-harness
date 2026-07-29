"""Hard gates pack — fail closed evidence for /pr_review."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import hard_gates as hg  # noqa: E402


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class TestHardGates(unittest.TestCase):
    def test_prose_only_skips_review_and_behavior(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "## What\n"
                "**Spec waiver:** docs-only\n"
                "## Red-proof\nTDD N/A docs-only\n",
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(True, False)):
                r = hg.evaluate(root, draft, diff=None)
            self.assertTrue(r.ok, r.violations)
            self.assertFalse(any("CODE-REVIEW" in v for v in r.violations))

    def test_code_ship_requires_code_review(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "**Spec:** .agents/specs/x.md\n"
                "## Red-proof\n- red_cmd: pytest -q t\n- green_cmd: pytest -q t\n"
                "## Traceability\n| AC | Test |\n| AC-1 | pytest |\n",
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(False, False)):
                with mock.patch.object(hg, "_secrets_ok", return_value=True):
                    r = hg.evaluate(root, draft, diff="HEAD~1...HEAD")
            self.assertFalse(r.ok)
            self.assertTrue(any("CODE-REVIEW" in v for v in r.violations))

    def test_code_review_marker_ok(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "**Spec waiver:** chore\n"
                "## Red-proof\n- red_cmd: true\n- green_cmd: true\nTDD done\n"
                "## Traceability\n| AC-1 | tests/test_x.py |\n| smoke | product_smoke |\n",
            )
            _write(
                root / ".agents" / "artifacts" / "CODE_REVIEW.md",
                "# CODE-REVIEW\n**Marker:** CODE-REVIEW\np0=0\n",
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(False, False)):
                with mock.patch.object(hg, "_secrets_ok", return_value=True):
                    r = hg.evaluate(root, draft, diff=None)
            self.assertTrue(r.ok, r.violations)

    def test_runtime_requires_behavior(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "**Spec:** .agents/specs/x.md\n"
                "## Red-proof\nred_cmd: x\ngreen_cmd: y\n"
                "## Traceability\n| AC-1 | pytest |\n"
                "## Threat notes\n- asset: API\n- abuse: injection\n",
            )
            _write(
                root / ".agents" / "artifacts" / "CODE_REVIEW.md",
                "CODE-REVIEW\n",
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(False, True)):
                with mock.patch.object(hg, "_secrets_ok", return_value=True):
                    r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("BEHAVIOR" in v for v in r.violations))

    def test_spec_or_waiver_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(draft, "## Red-proof\nTDD N/A\n")
            with mock.patch.object(hg, "_scope_flags", return_value=(True, False)):
                r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("Spec" in v for v in r.violations))

    def test_red_proof_required_for_code(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "**Spec waiver:** hotfix\nNo tests mentioned.\n"
                "## Traceability\n| AC-1 | n/a |\n",
            )
            _write(
                root / ".agents" / "artifacts" / "CODE_REVIEW.md",
                "CODE-REVIEW\n",
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(False, False)):
                with mock.patch.object(hg, "_secrets_ok", return_value=True):
                    r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("Red-proof" in v or "red" in v.lower() for v in r.violations))


if __name__ == "__main__":
    unittest.main()
