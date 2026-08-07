"""web_e2e_contract + check_web_e2e."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from web_e2e_contract import allocate_scenario_ids, detect_website, validate_web_e2e  # noqa: E402


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
    # re-run same order
    assert [x["global_id"] for x in allocate_scenario_ids(surfaces)] == ["S0", "S1", "S2"]


def test_detect_no_website(tmp_path: Path):
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents" / "product_plugin.yaml").write_text("product_id: x\n", encoding="utf-8")
    d = detect_website(tmp_path)
    assert d["has_website"] is False


def test_detect_web_dir(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    d = detect_website(tmp_path)
    assert d["has_website"] is True
    assert "web/" in d["reasons"]


def test_validate_fails_without_artifacts(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    r = validate_web_e2e(tmp_path)
    assert r["has_website"] is True
    assert r["pass"] is False
    assert any("Comet" in v or "playwright" in v for v in r["violations"])


def test_validate_passes_minimal(tmp_path: Path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web" / "index.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "E2E_COMET_SCENARIOS.md").write_text(
        "# x\nPROMPT FOR COMET\nReport template\nplaywright e2e/\n",
        encoding="utf-8",
    )
    (tmp_path / "e2e").mkdir()
    (tmp_path / "e2e" / "home.spec.ts").write_text("test('x', async () => {});", encoding="utf-8")
    (tmp_path / "playwright.config.ts").write_text("export default {}", encoding="utf-8")
    r = validate_web_e2e(tmp_path)
    assert r["pass"] is True


def test_cli_check_web_e2e():
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_web_e2e.py"), "--root", str(ROOT), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    # harness repo itself may or may not have website; must not crash
    assert r.returncode in (0, 1)
    data = json.loads(r.stdout)
    assert "has_website" in data
