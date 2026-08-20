#!/usr/bin/env python3
"""Night shift / readiness must NOT write or upsert agent-tasks/kanban.md."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "night_shift_readiness",
    ROOT / "scripts" / "night_shift_readiness.py",
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = """# Agent Kanban

## Done

- [x] **T-20260710-01** — other (2026-07-10)
  - notes: keep me
"""


class TestNightShiftDoesNotWriteKanban(unittest.TestCase):
    def test_upsert_is_noop_unchanged(self):
        out, msg = mod.upsert_kanban_readiness_done(
            SAMPLE,
            product_id="zk-business-card",
            overall="PASS",
            when_iso="2026-08-19T19:16:00Z",
            gate_summary="5/5",
        )
        self.assertEqual(out, SAMPLE)
        self.assertIn("no-op", msg.lower())
        self.assertNotIn("auto:night_shift_readiness", out)
        self.assertNotIn("T-NS-", out)

    def test_sync_never_writes_kanban_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            kanban = vault / "agent-tasks" / "kanban.md"
            kanban.parent.mkdir(parents=True)
            kanban.write_text(SAMPLE, encoding="utf-8")
            before = kanban.read_text(encoding="utf-8")
            msg = mod.sync_kanban_readiness_file(
                vault,
                product_id="zk-business-card",
                overall="PASS",
                when=datetime(2026, 8, 19, 19, 16, tzinfo=timezone.utc),
                results=[{"name": "hardcodes", "ok": True}],
                dry_run=False,
            )
            after = kanban.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertIn("no-op", msg.lower())
            self.assertTrue(kanban.is_file())

    def test_sync_does_not_create_missing_kanban(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "agent-tasks").mkdir(parents=True)
            kanban = vault / "agent-tasks" / "kanban.md"
            self.assertFalse(kanban.exists())
            msg = mod.sync_kanban_readiness_file(
                vault,
                product_id="zk-business-card",
                overall="PASS",
                when=datetime(2026, 8, 19, 19, 16, tzinfo=timezone.utc),
                results=[],
                dry_run=False,
            )
            self.assertFalse(kanban.exists())
            self.assertIn("no-op", msg.lower())

    def test_write_vault_does_not_touch_kanban(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            kanban = vault / "agent-tasks" / "kanban.md"
            kanban.parent.mkdir(parents=True)
            kanban.write_text(SAMPLE, encoding="utf-8")
            before = kanban.read_text(encoding="utf-8")
            notes = mod.write_vault(
                vault,
                Path("01-Projects/zk-business-card"),
                report_md="# report\n",
                todo_md="# TODO\n",
                when=datetime(2026, 8, 19, 19, 16, tzinfo=timezone.utc),
                overall="PASS",
                product_id="zk-business-card",
                dry_run=False,
                results=[{"name": "hardcodes", "ok": True}],
            )
            after = kanban.read_text(encoding="utf-8")
            self.assertEqual(before, after)
            joined = " ".join(notes).lower()
            self.assertNotIn("kanban.md", joined)
            self.assertFalse(any("kanban: insert" in n.lower() for n in notes))
            self.assertFalse(any("kanban: refresh" in n.lower() for n in notes))

    def test_kanban_auto_marker_removed(self):
        self.assertFalse(hasattr(mod, "KANBAN_AUTO_MARKER"))


if __name__ == "__main__":
    unittest.main()
