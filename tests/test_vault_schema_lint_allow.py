"""Vault schema allows the live night-shift layout and still rejects strangers."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vault_schema_lint as vsl  # noqa: E402


def _write_plugin(prod: Path, label: str) -> None:
    (prod / ".agents").mkdir(parents=True)
    (prod / ".agents" / "product_plugin.yaml").write_text(
        f"product_id: {label}\nvault:\n  project_label: {label}\n",
        encoding="utf-8",
    )


def _run(vault: Path, products: Path) -> int:
    argv = [
        "vault_schema_lint.py",
        "--vault",
        str(vault),
        "--products-file",
        str(products),
        "--report",
        str(vault / "schema-lint-report.md"),
        "--strict-warn",
    ]
    old = sys.argv
    try:
        sys.argv = argv
        return vsl.main()
    finally:
        sys.argv = old


class TestVaultSchemaAllow(unittest.TestCase):
    def test_registered_product_challenges_index_and_root_lodges(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            vault = root / "vault"
            proj = vault / "01-Projects" / "mission-feeds"
            (proj / "challenges").mkdir(parents=True)
            (proj / "docs").mkdir()
            (proj / "challenges" / "note.md").write_text("# c\n", encoding="utf-8")
            for name in ("dev-log.md", "night-shift-log.md", "TODO.md", "INDEX.md", "decisions.md"):
                (proj / name).write_text("# x\n", encoding="utf-8")
            (vault / "instruction-versions").mkdir()
            (vault / "rules").mkdir()
            herm = vault / "01-Projects" / "herm-config"
            herm.mkdir(parents=True)
            (herm / "README.md").write_text("# herm\n", encoding="utf-8")
            (herm / "INDEX.md").write_text("# index\n", encoding="utf-8")
            prod = root / "mission-feeds"
            _write_plugin(prod, "mission-feeds")
            products = root / "night_shift_products.yaml"
            products.write_text(f"mission-feeds: {prod}\n", encoding="utf-8")
            self.assertEqual(_run(vault, products), 0)

    def test_unregistered_project_and_unknown_root_still_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            vault = root / "vault"
            stray = vault / "01-Projects" / "not-a-product"
            stray.mkdir(parents=True)
            (stray / "TODO.md").write_text("# x\n", encoding="utf-8")
            (vault / "not-allowed-root").mkdir()
            products = root / "night_shift_products.yaml"
            products.write_text("", encoding="utf-8")
            rc = _run(vault, products)
            self.assertNotEqual(rc, 0)
            report = (vault / "schema-lint-report.md").read_text(encoding="utf-8")
            self.assertIn("not-a-product", report)
            self.assertIn("not-allowed-root", report)

    def test_herm_config_rejects_a_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            vault = root / "vault"
            herm = vault / "01-Projects" / "herm-config" / "secrets"
            herm.mkdir(parents=True)
            products = root / "night_shift_products.yaml"
            products.write_text("", encoding="utf-8")
            rc = _run(vault, products)
            self.assertNotEqual(rc, 0)
            report = (vault / "schema-lint-report.md").read_text(encoding="utf-8")
            self.assertIn("unexpected dir", report)

    def test_products_yaml_mission_feeds_path_is_portable(self) -> None:
        text = (ROOT / "config" / "night_shift_products.yaml").read_text(encoding="utf-8")
        row = ""
        for line in text.splitlines():
            if line.startswith("mission-feeds:"):
                row = line.split(":", 1)[1].strip()
        self.assertTrue(row.startswith("~/") or row.startswith("$HOME"), row)
        self.assertNotIn("/home/", row)


if __name__ == "__main__":
    unittest.main()
