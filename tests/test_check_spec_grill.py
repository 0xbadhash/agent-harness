#!/usr/bin/env python3
"""Tests for grill-me evidence gate."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_spec_grill as csg  # noqa: E402


COMPLETE = """# Spec

## Grill-me

**Status:** complete
**Date:** 2026-08-15

### G1 Outcome
- Q: Done looks like?
  - A: Ship grill default.
### G2 Non-goal
- Q: Kill what?
  - A: Multi-agent runtime.
### G3 Wrong product
- Q: Right repo?
  - A: agent-harness.
"""

SPIKE = """# Spec

## Grill-me

**Status:** spike-skipped
**Date:** 2026-08-15
**Reason:** True one-hour spike to measure API latency only.
"""

MISSING = """# Spec

## Acceptance Criteria

- [ ] foo
"""


class TestCheckSpecGrill(unittest.TestCase):
    def test_ac_complete(self):
        ok, msgs = csg.check_spec_text(COMPLETE)
        self.assertTrue(ok, msgs)

    def test_ac_spike(self):
        ok, msgs = csg.check_spec_text(SPIKE)
        self.assertTrue(ok, msgs)

    def test_missing_section(self):
        ok, msgs = csg.check_spec_text(MISSING)
        self.assertFalse(ok)
        self.assertTrue(any("Grill-me" in m for m in msgs))

    def test_spike_short_reason(self):
        bad = SPIKE.replace(
            "True one-hour spike to measure API latency only.",
            "short",
        )
        ok, _ = csg.check_spec_text(bad)
        self.assertFalse(ok)

    def test_waiver_skips_pr_draft(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text(
                "**Spec waiver:** hotfix\n", encoding="utf-8"
            )
            ok, msgs = csg.check_from_pr_draft(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)

    def test_pr_draft_linked_spec(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sp = root / "docs" / "specs" / "s.md"
            sp.parent.mkdir(parents=True)
            sp.write_text(COMPLETE, encoding="utf-8")
            (root / "PR_DRAFT.md").write_text(
                f"**Spec:** docs/specs/s.md\n", encoding="utf-8"
            )
            ok, msgs = csg.check_from_pr_draft(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)


if __name__ == "__main__":
    unittest.main()
