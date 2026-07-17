"""ORCH-P3b: coverage config + enforce from JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_module_coverage as cov  # noqa: E402


def test_config_only_ok(tmp_path: Path):
    cfg = tmp_path / "coverage_config.json"
    cfg.write_text(json.dumps({"default": 80, "modules": {"scripts/": 50}}), encoding="utf-8")
    assert cov.main(["--config", str(cfg)]) == 0


def test_config_only_bad(tmp_path: Path):
    cfg = tmp_path / "coverage_config.json"
    cfg.write_text(json.dumps({"modules": {}}), encoding="utf-8")
    assert cov.main(["--config", str(cfg)]) == 1


def test_enforce_from_json_pass(tmp_path: Path):
    cfg = tmp_path / "coverage_config.json"
    cfg.write_text(
        json.dumps(
            {
                "default": 50,
                "fail_under": 50,
                "modules": {"scripts/": 50},
                "exclude": [],
            }
        ),
        encoding="utf-8",
    )
    data = {
        "totals": {"percent_covered": 90.0},
        "files": {
            "scripts/foo.py": {"summary": {"percent_covered": 95.0}},
        },
    }
    j = tmp_path / "coverage.json"
    j.write_text(json.dumps(data), encoding="utf-8")
    assert cov.main(["--config", str(cfg), "--from-json", str(j)]) == 0


def test_enforce_from_json_fail_overall(tmp_path: Path):
    cfg = tmp_path / "coverage_config.json"
    cfg.write_text(
        json.dumps({"default": 80, "fail_under": 80, "modules": {}, "exclude": []}),
        encoding="utf-8",
    )
    data = {"totals": {"percent_covered": 10.0}, "files": {}}
    j = tmp_path / "coverage.json"
    j.write_text(json.dumps(data), encoding="utf-8")
    assert cov.main(["--config", str(cfg), "--from-json", str(j)]) == 1


def test_enforce_module_skip_zero(tmp_path: Path):
    cfg_dict = {
        "default": 80,
        "fail_under": 10,
        "modules": {"tests/": 0, "scripts/": 50},
        "exclude": [],
    }
    data = {
        "totals": {"percent_covered": 50.0},
        "files": {
            "tests/t.py": {"summary": {"percent_covered": 0.0}},
            "scripts/x.py": {"summary": {"percent_covered": 60.0}},
        },
    }
    ok, msgs = cov.enforce_coverage_json(data, cfg_dict)
    assert ok, msgs
    assert not any("tests/t.py" in m and m.startswith("❌") for m in msgs)


def test_soft_if_missing_run(tmp_path: Path, monkeypatch):
    cfg = tmp_path / "coverage_config.json"
    cfg.write_text(json.dumps({"default": 80}), encoding="utf-8")
    monkeypatch.setattr(cov, "_coverage_available", lambda py: False)
    # Point ROOT-less by only using --from-json soft path via --run soft
    rc = cov.main(["--config", str(cfg), "--run", "--soft-if-missing"])
    assert rc == 0
