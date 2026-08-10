#!/usr/bin/env python3
"""HSQ-2: FSM transition matrix."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pipeline_state as ps  # noqa: E402


class TestTransitions(unittest.TestCase):
    def _iso(self, td: str):
        return mock.patch.object(ps, "_state_path", return_value=Path(td) / "pipeline.json"), mock.patch.object(
            ps, "_lock_path", return_value=Path(td) / "lock"
        )

    def test_illegal_init_to_shipped(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(ps, "_state_path", return_value=Path(td) / "p.json"):
                with mock.patch.object(ps, "_lock_path", return_value=Path(td) / "l"):
                    with mock.patch.object(ps, "_root", return_value=Path(td)):
                        ps.set_phase("init")
                        with self.assertRaises(ValueError):
                            ps.set_phase("shipped")

    def test_force_transition_logs(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(ps, "_state_path", return_value=Path(td) / "p.json"):
                with mock.patch.object(ps, "_lock_path", return_value=Path(td) / "l"):
                    with mock.patch.object(ps, "_root", return_value=Path(td)):
                        ps.set_phase("init")
                        ps.set_phase(
                            "shipped",
                            force_transition=True,
                            force_reason="unit-test",
                        )
                        log = Path(td) / ".agents" / "artifacts" / "FORCE_TRANSITION_LOG.jsonl"
                        self.assertTrue(log.is_file())
                        self.assertIn("shipped", log.read_text(encoding="utf-8"))

    def test_ready_to_approved(self):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(ps, "_state_path", return_value=Path(td) / "p.json"):
                with mock.patch.object(ps, "_lock_path", return_value=Path(td) / "l"):
                    with mock.patch.object(ps, "_root", return_value=Path(td)):
                        ps.set_phase("init")
                        ps.set_phase("ready_for_review")
                        ps.set_phase("approved", score=100)
                        self.assertEqual(ps.get()["phase"], "approved")


if __name__ == "__main__":
    unittest.main()
