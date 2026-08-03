"""session_context Organize pack."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import session_context as sc  # noqa: E402


class TestSessionContext(unittest.TestCase):
    def test_build_and_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            st = t / ".agents" / "state"
            st.mkdir(parents=True)
            (st / "pipeline.json").write_text(
                json.dumps({"phase": "init", "score": 100, "task": "x"}),
                encoding="utf-8",
            )
            (t / "CHANGELOG.md").write_text(
                "## Open work\n\n### [OPEN] Example item\n",
                encoding="utf-8",
            )
            ctx = sc.build(t)
            self.assertEqual(ctx.phase, "init")
            self.assertIn("Example item", ctx.open_roadmap)
            md = sc.to_markdown(ctx)
            self.assertIn("SESSION_CONTEXT", md)
            self.assertIn("Organize", md)

    def test_cli_write(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            st = t / ".agents" / "state"
            st.mkdir(parents=True)
            (st / "pipeline.json").write_text(
                json.dumps({"phase": "approved", "score": 95}),
                encoding="utf-8",
            )
            rc = sc.main(["--root", str(t), "--write"])
            self.assertEqual(rc, 0)
            out = t / ".agents" / "artifacts" / "SESSION_CONTEXT.md"
            self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
