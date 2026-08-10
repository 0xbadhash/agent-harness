#!/usr/bin/env python3
"""HSQ-1 AC-2: waiver log append."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from spec_gate import append_waiver_log, check  # noqa: E402


class TestWaiverLog(unittest.TestCase):
    def test_append_and_check(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".agents" / "state").mkdir(parents=True)
            (root / ".agents" / "state" / "pipeline.json").write_text(
                json.dumps({"phase": "init"}), encoding="utf-8"
            )
            (root / "PR_DRAFT.md").write_text(
                "# PR\n\n**Spec waiver:** chore\n", encoding="utf-8"
            )
            ok, msgs = check(root, log_waiver=True)
            self.assertTrue(ok)
            log = root / ".agents" / "artifacts" / "WAIVER_LOG.jsonl"
            self.assertTrue(log.is_file())
            rows = [
                json.loads(line)
                for line in log.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["waiver_type"], "chore")

    def test_append_direct(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = append_waiver_log(root, waiver_type="hotfix", reason="unit")
            self.assertIsNotNone(p)
            assert p is not None
            self.assertTrue(p.is_file())


if __name__ == "__main__":
    unittest.main()
