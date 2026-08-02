"""remaining_board."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import remaining_board as rb  # noqa: E402


class TestRemaining(unittest.TestCase):
    def test_writes_open_items(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            (t / "CHANGELOG.md").write_text(
                "# C\n\n## Open work\n\n### [OPEN] Foo bar\n- x\n",
                encoding="utf-8",
            )
            st = t / ".agents" / "state"
            st.mkdir(parents=True)
            (st / "pipeline.json").write_text(
                json.dumps({"phase": "init"}), encoding="utf-8"
            )
            path = rb.write_board(t)
            text = path.read_text(encoding="utf-8")
            self.assertIn("REMAINING", text)
            self.assertIn("Foo bar", text)
            self.assertIn("init", text)


if __name__ == "__main__":
    unittest.main()
