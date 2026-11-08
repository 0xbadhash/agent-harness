"""project_rel must not invent the vault folder name ``product``."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vault_resolve  # noqa: E402


class TestProjectRelLabel(unittest.TestCase):
    def test_missing_plugin_uses_directory_name(self) -> None:
        """A fixture root with no plugin is filed under its own name.

        The old default label ``product`` created ``01-Projects/product/`` in the
        live vault when a test forgot to pass a vault, and schema lint then
        failed that unregistered folder.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "widget"
            root.mkdir()
            rel = vault_resolve.project_rel(root, "challenges", "note.md")
        self.assertEqual(rel, Path("01-Projects/widget/challenges/note.md"))

    def test_plugin_label_wins_over_directory_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "widget"
            (root / ".agents").mkdir(parents=True)
            (root / ".agents" / "product_plugin.yaml").write_text(
                "product_id: widget\nvault:\n  project_label: demo\n",
                encoding="utf-8",
            )
            rel = vault_resolve.project_rel(root, "decisions.md")
        self.assertEqual(rel, Path("01-Projects/demo/decisions.md"))

    def test_missing_plugin_config_does_not_default_label_to_product(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "widget"
            root.mkdir()
            cfg = vault_resolve.load_vault_config(root)
        self.assertEqual(cfg.get("project_label"), "")


if __name__ == "__main__":
    unittest.main()
