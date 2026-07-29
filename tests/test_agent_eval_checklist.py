"""C5 — agent_eval_checklist."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_eval_checklist as aec  # noqa: E402


class TestAgentEvalChecklist(unittest.TestCase):
    def test_harness_root_passes(self):
        r = aec.evaluate(ROOT, run_tests=False)
        self.assertTrue(r.ok, [c for c in r.checks if not c.ok])
        names = {c.name for c in r.checks}
        self.assertIn("pipeline_state", names)
        self.assertIn("next_skill", names)
        self.assertIn("hard_gates", names)

    def test_empty_root_fails(self):
        with tempfile.TemporaryDirectory() as td:
            r = aec.evaluate(Path(td), run_tests=False)
            self.assertFalse(r.ok)

    def test_cli_skip_tests(self):
        import subprocess

        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "agent_eval_checklist.py"),
                "--root",
                str(ROOT),
                "--skip-tests",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
