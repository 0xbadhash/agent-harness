#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from night_shift_log import render_log_document, strip_schedule_tables  # noqa: E402


SAMPLE = """# Night shift readiness — agent-harness — 2026-08-17

**Overall:** PASS

## When tests run (act map)

_SoT: `scripts/test_trigger_schedule.py` · ship chain + CI + night + ops._

| Phase | Clock | Tests | See | If red |
|-------|-------|-------|-----|--------|
| Ship: /spec | When | Spec | PR | Write |

### Ship chain order (human + agent)

`/spec` → `/execute_dev`

### Not the same as night

- **GitHub green** = CI

## Gates (this night run)

| Gate | Result |
|------|--------|
| hardcodes | ✅ |
"""


class TestScheduleStrip(unittest.TestCase):
    def test_strip_removes_act_map(self):
        out = strip_schedule_tables(SAMPLE)
        self.assertNotIn("## When tests run", out)
        self.assertIn("## Gates", out)

    def test_log_has_single_sot_link(self):
        doc = render_log_document("agent-harness", [("t", "PASS")], [SAMPLE, SAMPLE])
        self.assertEqual(doc.count("## When tests run"), 0)
        self.assertEqual(doc.count("Schedule SoT"), 1)


if __name__ == "__main__":
    unittest.main()
