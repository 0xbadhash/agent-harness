"""Markdown escape-hatch audit: prose cannot replace a check."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_markdown_audit as cma  # noqa: E402
import check_stale_agent_config as csac  # noqa: E402


def _skill(root: Path, body: str) -> None:
    p = root / "skills" / "demo" / "SKILL.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")


class TestAgentsBloat(unittest.TestCase):
    def test_over_cap_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("x\n" * 251, encoding="utf-8")
            ok, msgs = cma.check_agents_bloat(root)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("250" in m for m in msgs), msgs)

    def test_at_cap_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("x\n" * 250, encoding="utf-8")
            ok, msgs = cma.check_agents_bloat(root)
            self.assertTrue(ok, msgs)

    def test_missing_agents_md_skips(self):
        with tempfile.TemporaryDirectory() as td:
            ok, msgs = cma.check_agents_bloat(Path(td))
            self.assertTrue(ok, msgs)

    def test_stale_agent_config_calls_bloat(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "AGENTS.md").write_text("x\n" * 251, encoding="utf-8")
            ok, msgs = csac.check(root)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("AGENTS.md" in m for m in msgs), msgs)


class TestEscapeHatches(unittest.TestCase):
    def test_bullet_with_justification_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _skill(root, "# Demo\n\n- Skip the gate for now.\n")
            ok, msgs = cma.check(root)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("escape_hatch" in m for m in msgs), msgs)

    def test_bullet_naming_a_check_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _skill(
                root,
                "# Demo\n\n- Temporary shim; `scripts/check_repo_hygiene.py` fails if it survives.\n",
            )
            ok, msgs = cma.check(root)
            self.assertTrue(ok, msgs)

    def test_table_rows_are_not_rules(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _skill(root, "# Demo\n\n| No band-aids | No workarounds or temporary patches |\n")
            ok, msgs = cma.check(root)
            self.assertTrue(ok, msgs)


class TestDoNotEnforcement(unittest.TestCase):
    def test_unenforced_bullet_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _skill(root, "# Demo\n\n## Do not\n\n- Break the vault.\n")
            ok, msgs = cma.check(root)
            self.assertFalse(ok, msgs)
            self.assertTrue(any("unenforced" in m for m in msgs), msgs)

    def test_bullet_with_check_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _skill(
                root,
                "# Demo\n\n## Do not\n\n- Break the vault — check: `scripts/vault_schema_lint.py`.\n",
            )
            ok, msgs = cma.check(root)
            self.assertTrue(ok, msgs)

    def test_section_ends_at_next_heading(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _skill(
                root,
                "# Demo\n\n## Do not\n\n- Break the vault — check: `scripts/vault_schema_lint.py`.\n"
                "\n## Handoff\n\n- Plain prose without a check.\n",
            )
            ok, msgs = cma.check(root)
            self.assertTrue(ok, msgs)

    def test_live_tree_passes(self):
        ok, msgs = cma.check(ROOT)
        self.assertTrue(ok, msgs)


if __name__ == "__main__":
    unittest.main()
