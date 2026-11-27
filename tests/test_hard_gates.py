"""Hard gates pack — fail closed evidence for /pr_review."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_comment_audit as cca
import check_correction_checks as ccc
import check_lint_ratchet as clr
import check_markdown_audit as cma
import check_repo_hygiene as crh
import hard_gates as hg


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
                "## Red-proof\n- red_cmd: false\n- green_cmd: true\n"
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
                "## Red-proof\n- red_cmd: false\n- green_cmd: true\nTDD done\n"
                "## Traceability\n| AC-1 | tests/test_x.py |\n| smoke | product_smoke |\n"
                "## Evidence pack\n| hard_gates | ok |\n| smoke | product_smoke |\n",
            )
            _write(
                root / ".agents" / "artifacts" / "CODE_REVIEW.md",
                "# CODE-REVIEW\n**Marker:** CODE-REVIEW\n\n"
                "## Findings\n- No P0 issues in test fixture scope.\n"
                "- Gate checks exercised via unit tests.\n\n"
                "## Correction checks\n"
                "- fixture finding → tests/test_hard_gates.py\n\n"
                "## Verdict\nApprove fixture pass for hard_gates unit test.\n"
                + ("x" * 80),
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(False, False)):
                with mock.patch.object(hg, "_secrets_ok", return_value=True):
                    r = hg.evaluate(root, draft, diff=None)
            self.assertTrue(r.ok, r.violations)

    def test_evidence_pack_required_for_code(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "**Spec waiver:** chore\n"
                "## Red-proof\n- red_cmd: false\n- green_cmd: true\n"
                "## Traceability\n| AC-1 | tests/test_x.py |\n| smoke | product_smoke |\n",
            )
            _write(
                root / ".agents" / "artifacts" / "CODE_REVIEW.md",
                "CODE-REVIEW\n",
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(False, False)):
                with mock.patch.object(hg, "_secrets_ok", return_value=True):
                    r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("Evidence pack" in v for v in r.violations))

    def test_evidence_pack_thin_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "**Spec waiver:** chore\n"
                "## Red-proof\n- red_cmd: false\n- green_cmd: true\n"
                "## Traceability\n| AC-1 | tests/test_x.py |\n| smoke | product_smoke |\n"
                "## Evidence pack\nok\n",
            )
            _write(
                root / ".agents" / "artifacts" / "CODE_REVIEW.md",
                "CODE-REVIEW\n",
            )
            with mock.patch.object(hg, "_scope_flags", return_value=(False, False)):
                with mock.patch.object(hg, "_secrets_ok", return_value=True):
                    r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("Evidence pack" in v for v in r.violations))

    def test_prose_skips_evidence_pack(self):
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

    def test_runtime_requires_behavior(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "**Spec:** .agents/specs/x.md\n"
                "## Red-proof\nred_cmd: false\ngreen_cmd: true\n"
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

    def _valid_code_draft(self, root: Path) -> Path:
        draft = root / "PR_DRAFT.md"
        _write(
            draft,
            "**Spec waiver:** chore\n"
            "## Red-proof\n- red_cmd: false\n- green_cmd: true\nTDD done\n"
            "## Traceability\n| AC-1 | tests/test_x.py |\n| smoke | product_smoke |\n"
            "## Evidence pack\n| hard_gates | ok |\n| smoke | product_smoke |\n",
        )
        _write(
            root / ".agents" / "artifacts" / "CODE_REVIEW.md",
            "# CODE-REVIEW\n**Marker:** CODE-REVIEW\n\n"
            "## Findings\n- No P0 issues in fixture scope.\n\n"
            "## Correction checks\n- fixture finding → tests/test_hard_gates.py\n\n"
            "## Verdict\nApprove fixture pass.\n" + ("x" * 80),
        )
        return draft

    def test_new_checks_block_code_ship(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = self._valid_code_draft(root)
            with (
                mock.patch.object(hg, "_scope_flags", return_value=(False, False)),
                mock.patch.object(hg, "_secrets_ok", return_value=True),
                mock.patch.object(clr, "check", return_value=(False, ["E501 2 > 1"])),
                mock.patch.object(cca, "check", return_value=(False, ["history"])),
                mock.patch.object(ccc, "check", return_value=(False, ["missing section"])),
            ):
                r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            for name in ("lint_ratchet", "comment_audit", "correction_checks"):
                self.assertTrue(
                    any(name in v for v in r.violations), (name, r.violations)
                )

    def test_new_checks_skip_for_prose(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "## What\n**Spec waiver:** docs-only\n"
                "## Red-proof\nTDD N/A docs-only\n",
            )
            with (
                mock.patch.object(hg, "_scope_flags", return_value=(True, False)),
                mock.patch.object(clr, "check", return_value=(False, ["x"])),
                mock.patch.object(cca, "check", return_value=(False, ["x"])),
                mock.patch.object(ccc, "check", return_value=(False, ["x"])),
            ):
                r = hg.evaluate(root, draft, diff=None)
            self.assertTrue(r.ok, r.violations)
            self.assertTrue(any("lint_ratchet" in s for s in r.skipped))
            self.assertTrue(any("comment_audit" in s for s in r.skipped))
            self.assertTrue(any("correction_checks" in s for s in r.skipped))

    def test_repo_hygiene_blocks_code_ship(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = self._valid_code_draft(root)
            with (
                mock.patch.object(hg, "_scope_flags", return_value=(False, False)),
                mock.patch.object(hg, "_secrets_ok", return_value=True),
                mock.patch.object(clr, "check", return_value=(True, ["ok"])),
                mock.patch.object(cca, "check", return_value=(True, ["ok"])),
                mock.patch.object(ccc, "check", return_value=(True, ["ok"])),
                mock.patch.object(
                    crh, "check", return_value=(False, ["fail: scratch artifact x.bak-1"])
                ),
            ):
                r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("repo_hygiene" in v for v in r.violations), r.violations)

    def test_repo_hygiene_skips_for_prose(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = root / "PR_DRAFT.md"
            _write(
                draft,
                "## What\n**Spec waiver:** docs-only\n"
                "## Red-proof\nTDD N/A docs-only\n",
            )
            with (
                mock.patch.object(hg, "_scope_flags", return_value=(True, False)),
                mock.patch.object(crh, "check", return_value=(False, ["fail: x.bak-1"])),
            ):
                r = hg.evaluate(root, draft, diff=None)
            self.assertTrue(r.ok, r.violations)
            self.assertTrue(any("repo_hygiene" in s for s in r.skipped))

    def test_markdown_audit_blocks_code_ship(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            draft = self._valid_code_draft(root)
            with (
                mock.patch.object(hg, "_scope_flags", return_value=(False, False)),
                mock.patch.object(hg, "_secrets_ok", return_value=True),
                mock.patch.object(clr, "check", return_value=(True, ["ok"])),
                mock.patch.object(cca, "check", return_value=(True, ["ok"])),
                mock.patch.object(ccc, "check", return_value=(True, ["ok"])),
                mock.patch.object(crh, "check", return_value=(True, ["ok"])),
                mock.patch.object(
                    cma, "check", return_value=(False, ["fail: unenforced Do not bullet"])
                ),
            ):
                r = hg.evaluate(root, draft, diff=None)
            self.assertFalse(r.ok)
            self.assertTrue(any("markdown_audit" in v for v in r.violations), r.violations)


if __name__ == "__main__":
    unittest.main()
