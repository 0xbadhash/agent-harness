"""Install + verify_skills bootstrap tests (stdlib unittest — no pytest required)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
INSTALL = HARNESS / "install_into_product.sh"
VERIFY = HARNESS / "scripts" / "verify_skills.py"
BOOT_CHECK = HARNESS / "scripts" / "bootstrap_check.sh"
SHIP = HARNESS / "config" / "ship_skills.txt"


def _ship_names() -> list[str]:
    out = []
    for line in SHIP.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


class TestInstallBootstrap(unittest.TestCase):
    def test_ship_skills_exist_in_harness(self) -> None:
        for name in _ship_names():
            skill = HARNESS / "skills" / name / "SKILL.md"
            self.assertTrue(skill.is_file(), f"missing harness skill {name}")

    def test_verify_skills_harness_root(self) -> None:
        r = subprocess.run(
            [sys.executable, str(VERIFY), str(HARNESS)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ship-chain skills present", r.stdout)

    def test_install_into_temp_product(self) -> None:
        self.assertTrue(INSTALL.is_file())
        with tempfile.TemporaryDirectory(prefix="harness-install-") as td:
            product = Path(td)
            # minimal git-like product
            (product / "README.md").write_text("# tmp product\n", encoding="utf-8")
            r = subprocess.run(
                ["bash", str(INSTALL), str(product), "--verify"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("installed portable harness", r.stdout)

            for name in _ship_names():
                p = product / ".agents" / "skills" / name / "SKILL.md"
                self.assertTrue(p.is_file(), f"install missing {name}")

            self.assertTrue((product / ".agents" / "state" / "pipeline.json").is_file())
            self.assertTrue((product / ".agents" / "product_plugin.yaml").is_file())
            self.assertTrue((product / "scripts" / "pipeline_state.py").is_file())
            self.assertTrue((product / "scripts" / "next_skill.py").is_file())
            self.assertTrue((product / ".agents" / "docs" / "llm-bootstrap.md").is_file())
            self.assertTrue((product / ".agents" / "docs" / "ship-flow.md").is_file())
            self.assertTrue((product / "AGENTS.md").is_file())  # template when missing

            # verify_skills from product scripts against product root
            r2 = subprocess.run(
                [sys.executable, str(product / "scripts" / "verify_skills.py"), str(product)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

            r3 = subprocess.run(
                ["bash", str(product / "scripts" / "bootstrap_check.sh"), str(product)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r3.returncode, 0, r3.stdout + r3.stderr)

            # pipeline get
            r4 = subprocess.run(
                [sys.executable, str(product / "scripts" / "pipeline_state.py"), "get"],
                cwd=str(product),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r4.returncode, 0, r4.stdout + r4.stderr)
            self.assertIn("init", r4.stdout)

            # second install does not clobber product_plugin
            plugin = product / ".agents" / "product_plugin.yaml"
            plugin.write_text("product_id: custom\nproduct_name: Custom\n", encoding="utf-8")
            r5 = subprocess.run(
                ["bash", str(INSTALL), str(product)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r5.returncode, 0, r5.stdout + r5.stderr)
            self.assertIn("custom", plugin.read_text(encoding="utf-8"))
            self.assertIn("left as-is", r5.stdout)

    def test_install_preserves_product_only_skill(self) -> None:
        with tempfile.TemporaryDirectory(prefix="harness-install-") as td:
            product = Path(td)
            skill_dir = product / ".agents" / "skills" / "my_product_deploy"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: my_product_deploy\ndescription: product only\n---\n# deploy\n",
                encoding="utf-8",
            )
            r = subprocess.run(
                ["bash", str(INSTALL), str(product)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue((skill_dir / "SKILL.md").is_file())
            self.assertTrue(
                (product / ".agents" / "skills" / "execute_dev" / "SKILL.md").is_file()
            )


if __name__ == "__main__":
    unittest.main()
