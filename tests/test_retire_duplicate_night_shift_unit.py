"""Retirement plan for the duplicate watchlist night-shift unit."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "retire_duplicate_night_shift_unit.py"
    spec = importlib.util.spec_from_file_location(
        "retire_duplicate_night_shift_unit", path
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _units(directory: Path, *names: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_text(f"# {name}\n", encoding="utf-8")


def test_ac_1_watchlist_stays_in_registry():
    """AC-1: the product registry still names watchlist."""
    text = (ROOT / "config" / "night_shift_products.yaml").read_text(encoding="utf-8")
    mod = _load()
    assert "watchlist" in mod.product_ids(text)


def test_ac_2_plan_removes_only_duplicate_units(tmp_path: Path):
    """AC-2: remove list is only the two night-shift-readiness unit files."""
    _units(
        tmp_path,
        "night-shift-all.timer",
        "night-shift-all.service",
        "night-shift-readiness.timer",
        "night-shift-readiness.service",
        "other.timer",
    )
    mod = _load()
    plan = mod.plan_retirement(tmp_path, "watchlist: ~/watchlist\n")
    assert plan["ok"] is True
    removed = sorted(path.name for path in plan["remove"])
    assert removed == [
        "night-shift-readiness.service",
        "night-shift-readiness.timer",
    ]


def test_ac_3_refuses_without_survivor_timer(tmp_path: Path):
    """AC-3: no survivor timer means do not retire anything."""
    _units(tmp_path, "night-shift-readiness.timer", "night-shift-readiness.service")
    mod = _load()
    plan = mod.plan_retirement(tmp_path, "watchlist: ~/watchlist\n")
    assert plan["ok"] is False
    assert plan["remove"] == []
    assert "night-shift-all.timer" in plan["reason"]


def test_ac_4_refuses_without_watchlist(tmp_path: Path):
    """AC-4: missing watchlist coverage blocks retirement."""
    _units(
        tmp_path,
        "night-shift-all.timer",
        "night-shift-readiness.timer",
        "night-shift-readiness.service",
    )
    mod = _load()
    plan = mod.plan_retirement(tmp_path, "email-detach: ~/email-detach\n")
    assert plan["ok"] is False
    assert plan["remove"] == []
    assert "watchlist" in plan["reason"]


def test_ac_5_apply_archives_then_deletes_duplicates_only(tmp_path: Path):
    """AC-5: apply archives the duplicates and leaves the survivor."""
    unit_dir = tmp_path / "units"
    archive = tmp_path / "archive"
    _units(
        unit_dir,
        "night-shift-all.timer",
        "night-shift-all.service",
        "night-shift-readiness.timer",
        "night-shift-readiness.service",
    )
    mod = _load()
    plan = mod.plan_retirement(unit_dir, "watchlist: ~/watchlist\n")
    result = mod.apply_retirement(plan, archive_dir=archive)
    assert result["ok"] is True
    assert not (unit_dir / "night-shift-readiness.timer").exists()
    assert not (unit_dir / "night-shift-readiness.service").exists()
    assert (unit_dir / "night-shift-all.timer").is_file()
    assert (unit_dir / "night-shift-all.service").is_file()
    archived = sorted(path.name for path in archive.iterdir())
    assert archived == [
        "night-shift-readiness.service",
        "night-shift-readiness.timer",
    ]
    assert "night-shift-readiness.timer" in (archive / "night-shift-readiness.timer").read_text(
        encoding="utf-8"
    )


def test_ac_6_deploy_does_not_ship_duplicate_unit():
    """AC-6: the harness deploy directory has no night-shift-readiness unit."""
    deploy = ROOT / "deploy"
    names = {path.name for path in deploy.iterdir()}
    assert "night-shift-all.timer" in names
    assert "night-shift-all.service" in names
    assert "night-shift-readiness.timer" not in names
    assert "night-shift-readiness.service" not in names


def test_ac_7_second_plan_is_empty_when_already_retired(tmp_path: Path):
    """AC-7: a second pass removes nothing when the duplicate is already gone."""
    _units(tmp_path, "night-shift-all.timer", "night-shift-all.service")
    mod = _load()
    plan = mod.plan_retirement(tmp_path, "watchlist: ~/watchlist\n")
    assert plan["ok"] is True
    assert plan["remove"] == []


def test_apply_refuses_a_path_outside_the_duplicate_names(tmp_path: Path):
    """A forged plan cannot unlink the survivor."""
    survivor = tmp_path / "night-shift-all.timer"
    survivor.write_text("keep\n", encoding="utf-8")
    mod = _load()
    forged = {"ok": True, "remove": [survivor], "reason": "forged"}
    with pytest.raises(ValueError):
        mod.apply_retirement(forged, archive_dir=tmp_path / "archive")
    assert survivor.is_file()
