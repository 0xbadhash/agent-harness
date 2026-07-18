#!/usr/bin/env python3
"""TDD: canonical night-shift-log.md template (Timeline + dual UTC/HKT + newest-first)."""
from __future__ import annotations

import importlib.util
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    path = ROOT / rel
    if not path.is_file():
        pytest.fail(f"missing module under test: {rel}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def logmod():
    return _load("night_shift_log", "scripts/night_shift_log.py")


def _report(product: str, when: str, overall: str) -> str:
    return (
        f"# Night shift readiness — {product} — {when}\n"
        f"\n"
        f"**When:** {when}\n"
        f"**Overall:** {overall} (1/1 gates) · mode=`full` · product=`{product}`\n"
        f"**Repo:** `/tmp/{product}`\n"
        f"**Hard-stops:** no release, no push, no product auto-fix\n"
        f"**SoT:** agent-harness `scripts/night_shift_readiness.py`\n"
        f"\n"
        f"## Gates\n"
        f"\n"
        f"| Gate | Result | Exit |\n"
        f"|------|--------|------|\n"
        f"| repo_hygiene | ✅ | 0 |\n"
        f"\n"
        f"## Failures (tails)\n"
        f"\n"
        f"_None._\n"
        f"\n"
        f"## Recommendations\n"
        f"\n"
        f"1. ok\n"
    )


def test_format_when_dual_includes_utc_and_hkt(logmod):
    when = datetime(2026, 7, 18, 7, 7, tzinfo=timezone.utc)
    s = logmod.format_when_dual(when)
    assert "UTC" in s and "HKT" in s
    assert "2026-07-18 07:07 UTC" in s
    assert "2026-07-18 15:07 HKT" in s
    assert " · " in s


def test_first_prepend_creates_timeline_and_report(logmod, tmp_path: Path):
    log = tmp_path / "night-shift-log.md"
    when = "2026-07-18 07:07 UTC · 2026-07-18 15:07 HKT"
    body = _report("demo", when, "PASS")
    logmod.write_night_shift_log(
        log,
        product_id="demo",
        report_md=body,
        overall="PASS",
        when_label=when,
    )
    text = log.read_text(encoding="utf-8")
    assert text.startswith("# demo night-shift log")
    assert "## Timeline" in text
    assert "| When" in text and "| Result |" in text
    # Timeline row before full report
    t_idx = text.index("## Timeline")
    r_idx = text.index("# Night shift readiness — demo —")
    assert t_idx < r_idx
    assert when in text.split("## Timeline", 1)[1].split("# Night shift readiness", 1)[0]
    assert "| PASS" in text or "| PASS |" in text or re.search(r"\|\s*PASS\s*\|", text)


def test_second_prepend_newest_first(logmod, tmp_path: Path):
    log = tmp_path / "night-shift-log.md"
    older = "2026-07-18 06:36 UTC · 2026-07-18 14:36 HKT"
    newer = "2026-07-18 07:07 UTC · 2026-07-18 15:07 HKT"
    logmod.write_night_shift_log(
        log,
        product_id="demo",
        report_md=_report("demo", older, "FAIL"),
        overall="FAIL",
        when_label=older,
    )
    logmod.write_night_shift_log(
        log,
        product_id="demo",
        report_md=_report("demo", newer, "PASS"),
        overall="PASS",
        when_label=newer,
    )
    text = log.read_text(encoding="utf-8")
    # Only one Timeline section
    assert text.count("## Timeline") == 1
    timeline = text.split("## Timeline", 1)[1].split("\n---\n", 1)[0]
    # First data row is newer
    rows = [
        ln
        for ln in timeline.splitlines()
        if ln.strip().startswith("|")
        and "When" not in ln
        and not re.match(r"^\|\s*-+\s*\|", ln.strip())
    ]
    assert len(rows) >= 2, rows
    assert newer in rows[0]
    assert "PASS" in rows[0]
    assert older in rows[1]
    assert "FAIL" in rows[1]
    # Full reports: newer H1 before older H1
    first = text.index(f"# Night shift readiness — demo — {newer}")
    second = text.index(f"# Night shift readiness — demo — {older}")
    assert first < second


def test_legacy_utc_only_row_preserved(logmod, tmp_path: Path):
    log = tmp_path / "night-shift-log.md"
    legacy = """# demo night-shift log

Newest-first readiness reports.

# Night shift readiness — demo — 2026-07-17 12:10 UTC

**When:** 2026-07-17 12:10 UTC
**Overall:** PASS (1/1 gates) · mode=`full` · product=`demo`
**Repo:** `/tmp/demo`
**Hard-stops:** no release, no push, no product auto-fix
**SoT:** agent-harness `scripts/night_shift_readiness.py`

## Gates

| Gate | Result | Exit |
|------|--------|------|
| repo_hygiene | ✅ | 0 |

## Failures (tails)

_None._

## Recommendations

1. ok
"""
    log.write_text(legacy, encoding="utf-8")
    newer = "2026-07-18 07:07 UTC · 2026-07-18 15:07 HKT"
    logmod.write_night_shift_log(
        log,
        product_id="demo",
        report_md=_report("demo", newer, "FAIL"),
        overall="FAIL",
        when_label=newer,
    )
    text = log.read_text(encoding="utf-8")
    timeline = text.split("## Timeline", 1)[1].split("\n---\n", 1)[0]
    assert "2026-07-17 12:10 UTC" in timeline
    # Must not invent HKT for legacy-only row
    legacy_line = [ln for ln in timeline.splitlines() if "2026-07-17 12:10" in ln][0]
    assert "HKT" not in legacy_line


def test_rotate_compact_uses_same_template(logmod, tmp_path: Path):
    log = tmp_path / "night-shift-log.md"
    w1 = "2026-07-18 06:00 UTC · 2026-07-18 14:00 HKT"
    w2 = "2026-07-18 07:00 UTC · 2026-07-18 15:00 HKT"
    logmod.write_night_shift_log(
        log,
        product_id="demo",
        report_md=_report("demo", w1, "FAIL"),
        overall="FAIL",
        when_label=w1,
    )
    logmod.write_night_shift_log(
        log,
        product_id="demo",
        report_md=_report("demo", w2, "PASS"),
        overall="PASS",
        when_label=w2,
    )
    out = logmod.render_rotated_log(
        log.read_text(encoding="utf-8"),
        product_id="demo",
        keep_full_reports=1,
    )
    assert out.startswith("# demo night-shift log")
    assert "## Timeline" in out
    assert out.count("# Night shift readiness —") == 1
    assert w2 in out
    # Timeline still has both rows
    timeline = out.split("## Timeline", 1)[1].split("\n---\n", 1)[0]
    assert w1 in timeline and w2 in timeline
    assert "auto-rotated" not in out.lower()
