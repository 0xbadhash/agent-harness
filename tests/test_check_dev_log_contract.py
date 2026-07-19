#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "check_dev_log_contract",
    ROOT / "scripts" / "check_dev_log_contract.py",
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_ok_file(tmp_path: Path):
    p = tmp_path / "demo"
    p.mkdir()
    log = p / "dev-log.md"
    log.write_text(
        "# demo dev log\n\nNewest first. Times: UTC + HKT.\n\n"
        "## 2026-07-19 — good\n\n"
        "- **When:** 2026-07-19 12:00 UTC · 2026-07-19 20:00 HKT\n"
        "- **Kind:** note\n"
        "- **Repo**: demo\n",
        encoding="utf-8",
    )
    # check_file expects path under 01-Projects/name/dev-log.md — parent.name = demo
    assert mod.check_file(log) == []


def test_missing_when(tmp_path: Path):
    p = tmp_path / "demo"
    p.mkdir()
    log = p / "dev-log.md"
    log.write_text(
        "# demo\n\nNewest first. HKT\n\n## 2026-07-19 — bad\n\n- **Kind:** note\n",
        encoding="utf-8",
    )
    errs = mod.check_file(log)
    assert any("When" in e for e in errs)


if __name__ == "__main__":
    from pathlib import Path as P
    import tempfile

    d = P(tempfile.mkdtemp())
    test_ok_file(d / "a")
    test_missing_when(d / "b")
    print("ok")
