"""Correction -> check map in CODE-REVIEW (T2087U item 1)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_correction_checks as ccc  # noqa: E402


def _review(root: Path, text: str) -> None:
    p = root / ".agents" / "artifacts" / "CODE_REVIEW.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


BASE = "# CODE-REVIEW\n**Marker:** CODE-REVIEW\n\n## Findings\n- P0 none\n"


class TestCorrectionChecks(unittest.TestCase):
    def test_missing_section_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _review(root, BASE)
            ok, msgs = ccc.check(root)
            self.assertFalse(ok)
            self.assertTrue(any("Correction checks" in m for m in msgs))

    def test_empty_review_skips(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ok, msgs = ccc.check(root)
            self.assertTrue(ok, msgs)

    def test_check_mapping_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _review(
                root,
                BASE
                + "\n## Correction checks\n"
                "- stale fixture TODO → tests/test_correction_checks.py\n"
                "- prose-only nit → no-check: wording is not machine-checkable\n",
            )
            ok, msgs = ccc.check(root)
            self.assertTrue(ok, msgs)

    def test_none_marker_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _review(root, BASE + "\n## Correction checks\n- none (no accepted findings)\n")
            ok, msgs = ccc.check(root)
            self.assertTrue(ok, msgs)

    def test_bullet_without_mapping_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _review(
                root,
                BASE + "\n## Correction checks\n- fixed by hand in review\n",
            )
            ok, msgs = ccc.check(root)
            self.assertFalse(ok)
            self.assertTrue(any("unmapped" in m for m in msgs), msgs)

    def test_no_check_short_reason_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _review(root, BASE + "\n## Correction checks\n- nit → no-check: meh\n")
            ok, msgs = ccc.check(root)
            self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
