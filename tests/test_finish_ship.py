"""finish_ship push proof."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import finish_ship as fs  # noqa: E402


class TestFinishShip(unittest.TestCase):
    def test_plan_for_phase(self):
        self.assertIn("execute_dev", fs._plan_for_phase("init"))
        self.assertEqual(fs._plan_for_phase("approved")[0], "release_mgmt")

    def test_evaluate_temp_git(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            subprocess.run(["git", "init"], cwd=t, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "t@t"],
                cwd=t,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "t"],
                cwd=t,
                check=True,
                capture_output=True,
            )
            (t / "f").write_text("x", encoding="utf-8")
            subprocess.run(["git", "add", "f"], cwd=t, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "i"],
                cwd=t,
                check=True,
                capture_output=True,
            )
            st = t / ".agents" / "state"
            st.mkdir(parents=True)
            (st / "pipeline.json").write_text(
                json.dumps({"phase": "shipped"}), encoding="utf-8"
            )
            proof = fs.evaluate(t, require_push=False)
            # fresh commit may still show dirty if init left hooks; write artifact either way
            path = fs.write_artifact(t, proof)
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertIn("PUSH_PROOF", text)
            self.assertIn("NEXT_SKILL plan", text)
            self.assertEqual(proof.phase, "shipped")


if __name__ == "__main__":
    unittest.main()
