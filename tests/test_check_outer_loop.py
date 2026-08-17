#!/usr/bin/env python3
"""Tests for outer-loop plan / tickets / plan-review gates."""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_outer_loop as col  # noqa: E402

GRILL = """
## Grill-me
**Status:** complete
### G1
- Q: Outcome?
  - A: Outer loop.
### G2
- Q: Non-goal?
  - A: Multi-agent runtime.
### G3
- Q: Product?
  - A: agent-harness.
"""

PLAN_THIN = "# Plan\n\nshort\n"

PLAN_OK = """# Plan: Outer loop

## Approach
Implement check_outer_loop and wire hard_gates.

## Architecture decisions
- scripts/check_outer_loop.py
- hard_gates integration

## Implementation sequence

1. Write check_outer_loop.py with plan/tickets/review rules
2. Wire into hard_gates evaluate path
3. Add plan_review skill and outer-loop playbook
4. Add unit tests and ship docs
5. Release 1.4.30 portfolio notes

## Testing plan
- unittest check_outer_loop
"""


class TestOuterLoop(unittest.TestCase):
    def test_waiver_skips(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "PR_DRAFT.md").write_text(
                "**Spec waiver:** hotfix\n", encoding="utf-8"
            )
            ok, msgs = col.check(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)

    def test_large_needs_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sp = root / "docs" / "specs" / "s.md"
            sp.parent.mkdir(parents=True)
            sp.write_text("# Spec\n" + GRILL, encoding="utf-8")
            (root / "PR_DRAFT.md").write_text(
                "**Spec:** docs/specs/s.md\n", encoding="utf-8"
            )
            with mock.patch.object(col, "_is_large", return_value=(True, "files")):
                ok, msgs = col.check(root, root / "PR_DRAFT.md")
            self.assertFalse(ok)
            self.assertTrue(any("Plan" in m for m in msgs))

    def test_large_with_plan_and_review(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sp = root / "docs" / "specs" / "s.md"
            pl = root / "docs" / "specs" / "s-plan.md"
            sp.parent.mkdir(parents=True)
            sp.write_text(
                "# Spec\n**Plan:** docs/specs/s-plan.md\n" + GRILL, encoding="utf-8"
            )
            # only 2 steps → tickets N/A
            pl.write_text(
                PLAN_OK.replace(
                    "1. Write check_outer_loop.py with plan/tickets/review rules\n"
                    "2. Wire into hard_gates evaluate path\n"
                    "3. Add plan_review skill and outer-loop playbook\n"
                    "4. Add unit tests and ship docs\n"
                    "5. Release 1.4.30 portfolio notes\n",
                    "1. Write check_outer_loop.py\n2. Wire hard_gates\n",
                ),
                encoding="utf-8",
            )
            art = root / ".agents" / "artifacts"
            art.mkdir(parents=True)
            (art / "PLAN_REVIEW.md").write_text(
                "# PLAN-REVIEW\n\n**Marker:** PLAN-REVIEW\n\n"
                "**Verdict:** PASS\n\n"
                "Finding 1: approach is clear and scoped to harness gates only.\n"
                "Finding 2: no security issues; local file evidence only.\n"
                "Finding 3: large-only default protects hotfixes from plan theater.\n",
                encoding="utf-8",
            )
            (root / "PR_DRAFT.md").write_text(
                "**Spec:** docs/specs/s.md\n**Plan:** docs/specs/s-plan.md\n",
                encoding="utf-8",
            )
            with mock.patch.object(col, "_is_large", return_value=(True, "files")):
                ok, msgs = col.check(root, root / "PR_DRAFT.md")
            self.assertTrue(ok, msgs)

    def test_tickets_required_for_many_steps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sp = root / "docs" / "specs" / "s.md"
            pl = root / "docs" / "specs" / "s-plan.md"
            sp.parent.mkdir(parents=True)
            sp.write_text("# Spec\n" + GRILL, encoding="utf-8")
            pl.write_text(PLAN_OK, encoding="utf-8")
            art = root / ".agents" / "artifacts"
            art.mkdir(parents=True)
            (art / "PLAN_REVIEW.md").write_text(
                "# PLAN-REVIEW\n**Marker:** PLAN-REVIEW\n**Verdict:** PASS\n"
                "Finding 1: ok.\nFinding 2: ok.\nMore text for length floor here.\n",
                encoding="utf-8",
            )
            (root / "PR_DRAFT.md").write_text(
                "**Spec:** docs/specs/s.md\n**Plan:** docs/specs/s-plan.md\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"OUTER_LOOP_TICKET_STEPS": "4"}):
                with mock.patch.object(col, "_is_large", return_value=(True, "files")):
                    ok, msgs = col.check(root, root / "PR_DRAFT.md")
            self.assertFalse(ok)
            self.assertTrue(any("Tickets" in m or "ticket" in m.lower() for m in msgs))

    def test_count_steps(self):
        self.assertGreaterEqual(col._count_plan_steps(PLAN_OK), 4)


if __name__ == "__main__":
    unittest.main()
