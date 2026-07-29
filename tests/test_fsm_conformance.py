"""C2 — FSM / skill routing self-tests."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import next_skill as ns  # noqa: E402
import pipeline_state as ps  # noqa: E402


class TestFsmConformance(unittest.TestCase):
    def test_illegal_phase_rejected(self):
        with self.assertRaises(ValueError):
            ps.set_phase("not_a_phase")

    def test_identity_fields_roundtrip(self):
        # Use isolated state path
        with mock.patch.object(ps, "_state_path") as sp:
            with mock.patch.object(ps, "_lock_path") as lp:
                import tempfile

                td = tempfile.mkdtemp()
                sp.return_value = Path(td) / "pipeline.json"
                lp.return_value = Path(td) / "lock"
                ps.set_phase(
                    "init",
                    score=1.0,
                    task="t",
                    spec_id="s.md",
                    card_id="T-1",
                    waiver=None,
                )
                # clear waiver explicitly
                data = ps.get()
                self.assertEqual(data["spec_id"], "s.md")
                self.assertEqual(data["card_id"], "T-1")
                self.assertEqual(data["phase"], "init")

    def test_sync_docs_small_skips_qa(self):
        with mock.patch.object(ns, "build_baseline", create=True):
            # force import path in decide — mock review_scope
            with mock.patch.dict("sys.modules", {}):
                pass
        with mock.patch(
            "review_scope.build_baseline",
            side_effect=Exception("no git"),
        ):
            nxt, meta = ns.decide(
                "sync_docs", base="a", head="b", repo=ROOT, force_qa=False
            )
        self.assertEqual(nxt, "(done)")
        self.assertIn(meta.get("qa"), ("skipped_small", "skipped"))

    def test_sync_docs_force_qa(self):
        nxt, meta = ns.decide(
            "sync_docs", base="a", head="b", repo=ROOT, force_qa=True
        )
        self.assertEqual(nxt, "/qa_campaign")
        self.assertEqual(meta.get("qa"), "suggested")


if __name__ == "__main__":
    unittest.main()
