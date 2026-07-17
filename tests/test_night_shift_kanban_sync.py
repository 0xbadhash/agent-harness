#!/usr/bin/env python3
"""TDD: night_shift readiness → kanban Done note upsert."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "night_shift_readiness",
    ROOT / "scripts" / "night_shift_readiness.py",
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


SAMPLE = """# Agent Kanban

## Backlog

- [ ] **T-20260711-01** — Enrich stubs
  - notes: old

## Doing

_(empty)_

## Blocked

_(empty)_

## Done

- [x] **T-20260710-01** — other (2026-07-10)
  - notes: keep me
"""


def test_skip_when_not_pass():
    out, msg = mod.upsert_kanban_readiness_done(
        SAMPLE,
        product_id="second-brain",
        overall="FAIL",
        when_iso="2026-07-17T12:00:00Z",
        gate_summary="3/5",
    )
    assert out == SAMPLE
    assert "skip" in msg.lower()


def test_insert_done_card_on_pass():
    out, msg = mod.upsert_kanban_readiness_done(
        SAMPLE,
        product_id="second-brain",
        overall="PASS",
        when_iso="2026-07-17T12:00:00Z",
        gate_summary="5/5 repo_hygiene,hardcodes",
    )
    assert "auto:night_shift_readiness" in out
    assert "Night shift readiness PASS" in out
    assert "5/5" in out
    assert "**T-20260710-01**" in out  # preserved
    assert "insert" in msg.lower() or "upsert" in msg.lower() or "wrote" in msg.lower()


def test_refresh_existing_auto_card():
    first, _ = mod.upsert_kanban_readiness_done(
        SAMPLE,
        product_id="second-brain",
        overall="PASS",
        when_iso="2026-07-17T12:00:00Z",
        gate_summary="5/5 a",
    )
    second, msg = mod.upsert_kanban_readiness_done(
        first,
        product_id="second-brain",
        overall="PASS",
        when_iso="2026-07-17T13:00:00Z",
        gate_summary="5/5 b",
    )
    assert second.count("auto:night_shift_readiness") == 1
    assert "5/5 b" in second
    assert "13:00:00Z" in second
    assert "refresh" in msg.lower() or "update" in msg.lower()


if __name__ == "__main__":
    test_skip_when_not_pass()
    test_insert_done_card_on_pass()
    test_refresh_existing_auto_card()
    print("ok")
