"""vault_schema_lint: night_shift yaml key may be a surface alias."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import vault_schema_lint as vsl


class TestVaultSchemaLintSurfaceAlias(unittest.TestCase):
    def test_ui_alias_to_catalyxt_ds_is_not_strict_warn(self) -> None:
        """yaml key `ui` + plugin product_id/label catalyxt-ds must exit 0."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            vault = root / "vault"
            (vault / "01-Projects" / "catalyxt-ds").mkdir(parents=True)
            for name in (
                "raw",
                "wiki",
                "agent-tasks",
                "00-Inbox",
                "02-Areas",
                "03-Resources",
                "04-Archive",
                "_templates",
                "_attachments",
            ):
                (vault / name).mkdir(exist_ok=True)
            for req in ("dev-log.md", "night-shift-log.md", "TODO.md"):
                (vault / "01-Projects" / "catalyxt-ds" / req).write_text("# x\n")

            prod = root / "catalyxt-ds"
            (prod / ".agents").mkdir(parents=True)
            (prod / ".agents" / "product_plugin.yaml").write_text(
                "product_id: catalyxt-ds\n"
                "vault:\n"
                "  project_label: catalyxt-ds\n"
            )
            products = root / "night_shift_products.yaml"
            products.write_text("ui: " + str(prod) + "\n")

            # Simulate argv main
            import sys

            argv = [
                "vault_schema_lint.py",
                "--vault",
                str(vault),
                "--products-file",
                str(products),
                "--report",
                str(vault / "agent-tasks" / "schema-lint-report.md"),
                "--strict-warn",
            ]
            old = sys.argv
            try:
                sys.argv = argv
                rc = vsl.main()
            finally:
                sys.argv = old
            self.assertEqual(rc, 0, "surface alias ui→catalyxt-ds must not fail strict-warn")


if __name__ == "__main__":
    unittest.main()
