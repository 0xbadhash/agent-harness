#!/usr/bin/env python3
"""TDD: ensure_dev_log seeds and normalizes Option A headers."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "ensure_dev_log",
    ROOT / "scripts" / "ensure_dev_log.py",
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_standard_header_has_option_a_and_newest_first():
    h = mod.standard_header("my-product")
    assert h.startswith("# my-product dev log")
    assert "Newest first" in h
    assert "sync_vault_devlog" in h
    assert "Option A" in h
    assert "Release" in h and "Note" in h


def test_ensure_creates_empty(tmp_path: Path):
    p = tmp_path / "dev-log.md"
    msg = mod.ensure_file(p, "demo", dry_run=False)
    assert "created" in msg
    text = p.read_text(encoding="utf-8")
    assert text.startswith("# demo dev log")
    assert "Newest first" in text


def test_ensure_normalizes_preserves_entries(tmp_path: Path):
    p = tmp_path / "dev-log.md"
    p.write_text(
        "# old title\n\nrandom intro\n\n## 2026-07-01 — note\n\n- x\n",
        encoding="utf-8",
    )
    msg = mod.ensure_file(p, "demo", dry_run=False)
    assert "normalized" in msg
    text = p.read_text(encoding="utf-8")
    assert text.startswith("# demo dev log")
    assert "## 2026-07-01 — note" in text
    assert "- x" in text
    # entry after header
    assert text.index("# demo") < text.index("## 2026-07-01")


def test_ensure_idempotent(tmp_path: Path):
    p = tmp_path / "dev-log.md"
    mod.ensure_file(p, "demo", dry_run=False)
    msg = mod.ensure_file(p, "demo", dry_run=False)
    assert "already standard" in msg
