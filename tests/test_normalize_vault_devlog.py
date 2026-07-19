#!/usr/bin/env python3
"""Tests for normalize_vault_devlog newest-first + When backfill."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "normalize_vault_devlog",
    ROOT / "scripts" / "normalize_vault_devlog.py",
)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = """# old header

## 2026-07-17 — older note

- **Repo**: x

## 2026-07-18 — newer note

- **Repo**: x

2026-07-08 — bare legacy line
"""


def test_newest_first_and_when_backfill():
    out = mod.normalize_text(SAMPLE, "demo")
    assert "Newest first" in out
    i_new = out.index("## 2026-07-18 — newer note")
    i_old = out.index("## 2026-07-17 — older note")
    i_bare = out.index("## 2026-07-08 — bare legacy line")
    assert i_new < i_old < i_bare
    # When on older entries
    assert out.count("**When:**") >= 3
    assert out.count("**Kind:**") >= 3


def test_release_kind():
    text = "# h\n\n## 2026-07-18 — v1.0.0 synced\n\n- **Scope:** x\n"
    out = mod.normalize_text(text, "p")
    assert "**Kind:** release" in out


if __name__ == "__main__":
    test_newest_first_and_when_backfill()
    test_release_kind()
    print("ok")
