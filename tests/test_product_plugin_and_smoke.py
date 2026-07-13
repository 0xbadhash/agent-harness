"""TDD: product_plugin load, path prefixes, smoke runner, suite_green rubric key."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_load_product_path_prefixes_from_plugin(tmp_path: Path):
    import product_plugin as pp  # type: ignore

    plugin = tmp_path / ".agents" / "product_plugin.yaml"
    plugin.parent.mkdir(parents=True)
    plugin.write_text(
        "product_path_prefixes:\n  - src/\n  - packages/core/\n",
        encoding="utf-8",
    )
    prefs = pp.load_product_path_prefixes(tmp_path)
    assert prefs == ["src/", "packages/core/"]


def test_load_product_path_prefixes_missing_plugin_returns_empty(tmp_path: Path):
    import product_plugin as pp  # type: ignore

    assert pp.load_product_path_prefixes(tmp_path) == []


def test_path_matches_prefix():
    import product_plugin as pp  # type: ignore

    assert pp.path_matches_product_prefixes("src/foo.ts", ["src/"]) is True
    assert pp.path_matches_product_prefixes("docs/x.md", ["src/"]) is False


def test_is_large_diff_uses_plugin_prefixes(monkeypatch, tmp_path: Path):
    import cross_review_gate as gate  # type: ignore

    plugin = tmp_path / ".agents" / "product_plugin.yaml"
    plugin.parent.mkdir(parents=True)
    plugin.write_text("product_path_prefixes:\n  - app/\n", encoding="utf-8")

    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(
        gate,
        "_git_diff_stat",
        lambda _d: ([f"app/f{i}.ts" for i in range(3)], 10),
    )
    large, detail = gate.is_large_diff("x")
    assert large is True
    assert "product_paths=3" in detail


def test_run_smoke_executes_cmds(tmp_path: Path):
    import product_smoke as smoke  # type: ignore

    agents = tmp_path / ".agents"
    agents.mkdir()
    (agents / "product_plugin.yaml").write_text(
        "smoke:\n"
        "  - name: ok\n"
        "    cmd: [\"python3\", \"-c\", \"print(1)\"]\n"
        "    cwd: .\n",
        encoding="utf-8",
    )
    results = smoke.run_smoke(tmp_path)
    assert len(results) == 1
    assert results[0]["name"] == "ok"
    assert results[0]["exit"] == 0


def test_run_smoke_fails_on_nonzero(tmp_path: Path):
    import product_smoke as smoke  # type: ignore

    agents = tmp_path / ".agents"
    agents.mkdir()
    (agents / "product_plugin.yaml").write_text(
        "smoke:\n"
        "  - name: bad\n"
        "    cmd: [\"python3\", \"-c\", \"raise SystemExit(2)\"]\n",
        encoding="utf-8",
    )
    results = smoke.run_smoke(tmp_path)
    assert results[0]["exit"] == 2


def test_run_smoke_empty_plugin_returns_empty(tmp_path: Path):
    import product_smoke as smoke  # type: ignore

    assert smoke.run_smoke(tmp_path) == []


def test_pr_validator_rubric_uses_suite_green_not_tdd_evidence():
    import pr_validator as pv  # type: ignore

    assert "suite_green" in pv.RUBRIC
    assert "tdd_evidence" not in pv.RUBRIC
    assert pv.RUBRIC["suite_green"] == 25
