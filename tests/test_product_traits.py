#!/usr/bin/env python3
"""Product-trait category gate — dry miss + web-only must not force isolation."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_product_traits as cpt  # noqa: E402
import product_trait_contract as ptc  # noqa: E402
from scaffold_web_e2e import render_spec_ts  # noqa: E402


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _web_only_fixture(td: Path) -> Path:
    """Website signals, no web3 / client_secrets."""
    _write(td / "web" / "index.html", "<html><body>hi</body></html>\n")
    _write(
        td / ".agents" / "product_plugin.yaml",
        "product_id: web-only-fixture\n"
        "traits:\n"
        "  web: true\n"
        "  web3: false\n"
        "  client_secrets: false\n"
        "web_e2e:\n"
        "  enabled: true\n"
        "  surfaces:\n"
        "    - id: home\n"
        "      order: 0\n"
        "      path: /\n"
        "      playwright: e2e/home.spec.ts\n"
        "      scenarios:\n"
        "        - id: smoke\n"
        "          name: Smoke load\n"
        "smoke:\n"
        "  - name: e2e\n"
        "    cmd: [npm, run, test:e2e]\n",
    )
    _write(
        td / "docs" / "E2E_COMET_SCENARIOS.md",
        "# Fixture\nPROMPT FOR COMET\nReport template\nPASS|FAIL\n"
        "### S0 — Smoke load\nPlaywright: e2e/home.spec.ts\n",
    )
    _write(
        td / "e2e" / "home.spec.ts",
        'import { test, expect } from "@playwright/test";\n'
        'test("S0 Smoke load", async ({ page }) => { await page.goto("/"); });\n',
    )
    _write(td / "playwright.config.ts", "export default {};\n")
    return td


def _web3_no_isolation_fixture(td: Path) -> Path:
    """web3 declared; Comet+Playwright smoke only — no isolation S-id (dry miss)."""
    _write(td / "web" / "index.html", "<html><body>card</body></html>\n")
    _write(
        td / "package.json",
        json.dumps(
            {
                "name": "card-like",
                "dependencies": {"@solana/web3.js": "1.0.0", "ethers": "6.0.0"},
            }
        )
        + "\n",
    )
    _write(
        td / ".agents" / "product_plugin.yaml",
        "product_id: web3-dry-miss\n"
        "traits:\n"
        "  web: true\n"
        "  web3: true\n"
        "  client_secrets: false\n"
        "web_e2e:\n"
        "  enabled: true\n"
        "  surfaces:\n"
        "    - id: home\n"
        "      order: 0\n"
        "      path: /\n"
        "      playwright: e2e/home.spec.ts\n"
        "      scenarios:\n"
        "        - id: smoke\n"
        "          name: Smoke load\n"
        "smoke:\n"
        "  - name: e2e\n"
        "    cmd: [npm, run, test:e2e]\n",
    )
    _write(
        td / "docs" / "E2E_COMET_SCENARIOS.md",
        "# Fixture\nPROMPT FOR COMET\nReport template\nPASS|FAIL\n"
        "### S0 — Smoke load\nPlaywright: e2e/home.spec.ts\n",
    )
    _write(
        td / "e2e" / "home.spec.ts",
        'import { test } from "@playwright/test";\n'
        'test("S0 Smoke load", async ({ page }) => { await page.goto("/"); });\n',
    )
    _write(td / "playwright.config.ts", "export default {};\n")
    return td


def _web3_with_isolation_fixture(td: Path) -> Path:
    _web3_no_isolation_fixture(td)
    _write(
        td / "docs" / "E2E_COMET_SCENARIOS.md",
        "# Fixture\nPROMPT FOR COMET\nReport template\nPASS|FAIL\n"
        "### S0 — Smoke load\nPlaywright: e2e/home.spec.ts\n"
        "### S1 — iso-two-holder — holder A never painted as holder B\n"
        "Playwright: e2e/home.spec.ts\n",
    )
    _write(
        td / "e2e" / "home.spec.ts",
        'import { test } from "@playwright/test";\n'
        'test("S0 Smoke load", async ({ page }) => { await page.goto("/"); });\n'
        'test("S1 iso-two-holder — holder A never painted as holder B; '
        'garbage id plain English", async ({ page }) => { await page.goto("/x"); });\n',
    )
    return td


class TestProductTraits(unittest.TestCase):
    def test_dry_miss_web3_without_isolation_exits_1(self):
        """CEO dry miss: web3 trait + no isolation S-id → EXIT 1."""
        with tempfile.TemporaryDirectory() as tmp:
            td = _web3_no_isolation_fixture(Path(tmp))
            ok, msgs = cpt.check(td)
            self.assertFalse(ok, msgs)
            self.assertTrue(
                any("isolation" in m and m.startswith("fail:") for m in msgs),
                msgs,
            )
            r = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_product_traits.py"), "--root", str(td)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_web_only_does_not_require_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = _web_only_fixture(Path(tmp))
            traits = ptc.infer_traits(td)
            self.assertTrue(traits["web"]["active"])
            self.assertFalse(traits["web3"]["active"])
            ok, msgs = cpt.check(td)
            self.assertTrue(ok, msgs)
            self.assertTrue(
                any("isolation stubs not required" in m for m in msgs),
                msgs,
            )

    def test_web3_with_isolation_passes_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = _web3_with_isolation_fixture(Path(tmp))
            ok, msgs = cpt.check(td)
            self.assertTrue(ok, msgs)
            self.assertTrue(any("isolation S-id" in m for m in msgs), msgs)

    def test_infer_web3_from_package_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            _write(
                td / "package.json",
                json.dumps({"dependencies": {"viem": "2.0.0"}}) + "\n",
            )
            _write(td / ".agents" / "product_plugin.yaml", "product_id: x\n")
            active, reasons = ptc.infer_web3(td)
            self.assertTrue(active, reasons)

    def test_named_stub_not_tautological(self):
        body = render_spec_ts(
            "home",
            "/",
            "Home",
            scenarios=[
                {
                    "global_id": "S1",
                    "local_id": "iso-two-holder",
                    "name": "iso-two-holder — holder A never painted as holder B",
                    "path": "/holders/wrong-id",
                    "steps": ["Assert plain English"],
                }
            ],
        )
        self.assertIn("S1 iso-two-holder", body)
        self.assertIn("test.skip", body)
        self.assertNotIn('toBeVisible()', body)
        self.assertIn("holder A never painted", body)

    def test_ensure_trait_scenarios_adds_isolation(self):
        surfaces = [
            {
                "id": "home",
                "path": "/",
                "playwright": "e2e/home.spec.ts",
                "scenarios": [{"id": "smoke", "name": "Smoke", "steps": ["open"]}],
            }
        ]
        traits = {
            "web3": {"active": True},
            "client_secrets": {"active": False},
        }
        out = ptc.ensure_trait_scenarios(surfaces, traits)
        self.assertTrue(ptc.surfaces_have_isolation(out))


if __name__ == "__main__":
    unittest.main()
