#!/usr/bin/env python3
"""TDD: newest-first prepend, UTC+HKT When, night_shift day dedupe."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "sync_vault_devlog",
    ROOT / "scripts" / "sync_vault_devlog.py",
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_format_when_utc_hkt_contains_both_zones():
    when = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
    line = mod.format_when_line(when)
    assert "UTC" in line and "HKT" in line
    assert "2026-07-18 12:00" in line  # UTC
    assert "2026-07-18 20:00" in line  # HKT = UTC+8


def test_split_header_and_rest():
    text = "# title\n\nintro\n\n## 2026-07-01 — old\n\n- x\n"
    header, rest = mod.split_header_and_rest(text)
    assert header.startswith("# title")
    assert rest.startswith("## 2026-07-01")


def test_prepend_puts_newest_first(tmp_path: Path | None = None):
    p = Path("/tmp") / "devlog-test-prepend.md"
    if p.exists():
        p.unlink()
    p.write_text(
        "# prod dev log\n\nNewest first.\n\n## 2026-07-01 — old\n\n- a\n",
        encoding="utf-8",
    )
    mod.prepend_entry(p, "## 2026-07-18 — new\n\n- b\n", init_header=False)
    text = p.read_text(encoding="utf-8")
    i_new = text.index("## 2026-07-18 — new")
    i_old = text.index("## 2026-07-01 — old")
    assert i_new < i_old
    p.unlink(missing_ok=True)


def test_build_note_has_when_and_kind():
    when = datetime(2026, 7, 18, 6, 30, tzinfo=timezone.utc)
    entry = mod.build_note_entry("Feature x", ["Outcome: ok"], when=when)
    assert "**When:**" in entry
    assert "**Kind:** note" in entry
    assert "HKT" in entry


def test_build_entry_has_when_and_kind():
    when = datetime(2026, 7, 18, 6, 30, tzinfo=timezone.utc)
    entry = mod.build_entry(
        tag="v1.0.0",
        runbook={"version": "v1.0.0", "scope": "test"},
        workflow_release="",
        pipeline_task="t1",
        shaping=[],
        synced_at=when,
    )
    assert "synced" in entry
    assert "**When:**" in entry
    assert "**Kind:** release" in entry


def test_night_shift_day_marker():
    m = mod.night_shift_day_marker(
        "Night shift readiness agent-harness 2026-07-18 PASS",
        day="2026-07-18",
        product_id="agent-harness",
    )
    assert m is not None
    assert "2026-07-18" in m
    assert "agent-harness" in m
    assert mod.night_shift_day_marker("Random note", day="2026-07-18", product_id="x") is None


if __name__ == "__main__":
    test_format_when_utc_hkt_contains_both_zones()
    test_split_header_and_rest()
    test_prepend_puts_newest_first()
    test_build_note_has_when_and_kind()
    test_build_entry_has_when_and_kind()
    test_night_shift_day_marker()
    print("ok")
