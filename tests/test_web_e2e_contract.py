"""web_e2e_contract + check_web_e2e — mandatory for website/app products."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from web_e2e_contract import (  # noqa: E402
    allocate_scenario_ids,
    detect_website,
    extract_playwright_scenario_ids,
    validate_web_e2e,
)


def _write_plugin(tmp: Path, body: str) -> None:
    (tmp / ".agents").mkdir(exist_ok=True)
    (tmp / ".agents" / "product_plugin.yaml").write_text(body, encoding="utf-8")


def test_allocate_ids_deterministic():
    surfaces = [
        {
            "id": "b",
            "order": 1,
            "path": "/b",
            "playwright": "e2e/b.spec.ts",
            "scenarios": [{"id": "smoke", "name": "B", "steps": ["open"]}],
        },
        {
            "id": "a",
            "order": 0,
            "path": "/",
            "playwright": "e2e/a.spec.ts",
            "scenarios": [
                {"id": "smoke", "name": "A0", "steps": ["open"]},
                {"id": "click", "name": "A1", "steps": ["click"]},
            ],
        },
    ]
    ids = allocate_scenario_ids(surfaces)
    assert [x["global_id"] for x in ids] == ["S0", "S1", "S2"]
    assert ids[0]["surface_id"] == "a"
    assert ids[2]["surface_id"] == "b"
    assert [x["global_id"] for x in allocate_scenario_ids(surfaces)] == ["S0", "S1", "S2"]


def test_detect_no_website(tmp_path: Path):
    _write_plugin(tmp_path, "product_id: x\n")
    d = detect_website(tmp_path)
    assert d["has_website"] is False


def test_detect_web_dir(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    d = detect_website(tmp_path)
    assert d["has_website"] is True
    assert "web/" in d["reasons"]


def test_detect_package_browser_framework(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react-dom": "18.0.0"},
                "scripts": {"test:e2e": "playwright test"},
            }
        ),
        encoding="utf-8",
    )
    d = detect_website(tmp_path)
    assert d["has_website"] is True


def test_opt_out_enabled_false(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    _write_plugin(tmp_path, "product_id: x\nweb_e2e:\n  enabled: false\n")
    d = detect_website(tmp_path)
    assert d["has_website"] is False


def test_validate_fails_without_artifacts(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    r = validate_web_e2e(tmp_path)
    assert r["has_website"] is True
    assert r["pass"] is False
    assert any("Comet" in v or "playwright" in v.lower() for v in r["violations"])


def test_validate_fails_without_smoke_e2e_and_surfaces(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "E2E_COMET_SCENARIOS.md").write_text(
        "# x\nPROMPT FOR COMET\nReport template\nplaywright e2e/\n### S0\n",
        encoding="utf-8",
    )
    (tmp_path / "e2e").mkdir()
    (tmp_path / "e2e" / "home.spec.ts").write_text(
        "test('S0 smoke load', async () => {});",
        encoding="utf-8",
    )
    (tmp_path / "playwright.config.ts").write_text("export default {}", encoding="utf-8")
    _write_plugin(tmp_path, "product_id: x\nsmoke: []\n")
    r = validate_web_e2e(tmp_path)
    assert r["pass"] is False
    joined = " ".join(r["violations"])
    assert "smoke" in joined
    assert "surfaces" in joined


def test_validate_passes_full_contract(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "E2E_COMET_SCENARIOS.md").write_text(
        "# x\nPROMPT FOR COMET\nReport template\nplaywright e2e/home.spec.ts\n### S0 — Smoke\n",
        encoding="utf-8",
    )
    (tmp_path / "e2e").mkdir()
    (tmp_path / "e2e" / "home.spec.ts").write_text(
        "test('S0 smoke load', async () => {});",
        encoding="utf-8",
    )
    (tmp_path / "playwright.config.ts").write_text("export default {}", encoding="utf-8")
    _write_plugin(
        tmp_path,
        "product_id: x\n"
        "smoke:\n"
        "  - name: e2e\n"
        "    cmd: [npm, run, test:e2e]\n"
        "web_e2e:\n"
        "  enabled: true\n"
        "  surfaces:\n"
        "    - id: home\n"
        "      order: 0\n"
        "      path: /\n"
        "      playwright: e2e/home.spec.ts\n"
        "      scenarios:\n"
        "        - id: smoke\n"
        "          name: Smoke\n"
        "          steps: [open]\n",
    )
    from product_plugin import load_plugin

    pl = load_plugin(tmp_path)
    assert pl.get("web_e2e", {}).get("surfaces"), pl
    r = validate_web_e2e(tmp_path)
    assert r["pass"] is True, r["violations"]
    assert "S0" in r["playwright_s_ids"]


def test_playwright_sid_missing_from_comet_fails(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "E2E_COMET_SCENARIOS.md").write_text(
        "# x\nPROMPT FOR COMET\nReport template\nplaywright e2e/\n### S0 only\n",
        encoding="utf-8",
    )
    (tmp_path / "e2e").mkdir()
    (tmp_path / "e2e" / "home.spec.ts").write_text(
        "test('S0 ok', async () => {});\ntest('S99 new feature', async () => {});",
        encoding="utf-8",
    )
    (tmp_path / "playwright.config.ts").write_text("export default {}", encoding="utf-8")
    _write_plugin(
        tmp_path,
        "product_id: x\n"
        "smoke:\n"
        "  - name: e2e\n"
        "    cmd: [npm, run, test:e2e]\n"
        "web_e2e:\n"
        "  enabled: true\n"
        "  surfaces:\n"
        "    - id: home\n"
        "      order: 0\n"
        "      path: /\n"
        "      playwright: e2e/home.spec.ts\n"
        "      scenarios:\n"
        "        - id: smoke\n"
        "          name: Smoke\n"
        "          steps: [open]\n",
    )
    r = validate_web_e2e(tmp_path)
    assert r["pass"] is False
    assert "S99" in r["missing_in_comet"]


def test_extract_playwright_ids(tmp_path: Path):
    p = tmp_path / "a.spec.ts"
    p.write_text(
        "test('S12 golden', async () => {});\ntest(\"S18b tools\", async () => {});",
        encoding="utf-8",
    )
    assert extract_playwright_scenario_ids([p]) == {"S12", "S18b"}


def test_cli_check_web_e2e():
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_web_e2e.py"), "--root", str(ROOT), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode in (0, 1)
    data = json.loads(r.stdout)
    assert "has_website" in data
