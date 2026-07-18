#!/usr/bin/env python3
"""Rotate vault night-shift logs: archive FAIL spam, keep timeline + latest report.

Run after readiness (or on a schedule) so operators are not buried in append-only FAIL history.

Usage:
  python3 scripts/rotate_night_shift_logs.py --vault /path/to/vault
  python3 scripts/rotate_night_shift_logs.py --vault ... --only agent-harness
  python3 scripts/rotate_night_shift_logs.py --vault ... --dry-run

Rules:
  - If latest Overall is PASS and log has older FAIL sections → archive full file, rewrite
    with a short timeline + latest PASS report (from NIGHT_SHIFT_REPORT.md if present).
  - If latest is FAIL → leave log intact (still valid debt); only rebuild multi SUMMARY.
  - Never invent gate results.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from night_shift_log import parse_reports as _parse_reports  # noqa: E402
from night_shift_log import render_rotated_log  # noqa: E402

_HOME = Path.home()
DEFAULT_VAULT = Path(
    os.environ.get("PRODUCT_VAULT_ROOT")
    or os.environ.get("WATCHLIST_VAULT_ROOT")
    or "/opt/second-brain/vault"
)


def rotate_project(
    project_dir: Path,
    *,
    dry_run: bool,
) -> str:
    log = project_dir / "night-shift-log.md"
    if not log.is_file():
        return f"skip {project_dir.name}: no night-shift-log.md"

    text = log.read_text(encoding="utf-8", errors="replace")
    reports = _parse_reports(text)
    if not reports:
        return f"skip {project_dir.name}: no report chunks"

    # Newest-first logs (after 2026-07-18): first chunk is latest; fall back to last
    latest = reports[0]
    fails = [r for r in reports if r["overall"] == "FAIL"]
    passes = [r for r in reports if r["overall"] == "PASS"]

    # Only rotate when we have historical FAIL noise and latest is PASS
    if latest["overall"] != "PASS":
        return (
            f"keep {project_dir.name}: latest={latest['overall']} "
            f"({len(fails)} FAIL in history — still valid or needs product fix)"
        )
    if len(fails) == 0 and len(reports) <= 2:
        return f"ok {project_dir.name}: already lean (latest PASS, little history)"

    when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    archive_dir = project_dir / "_archive"
    archive_path = archive_dir / f"night-shift-log-through-{when}.md"

    # Prefer freshest product artifact report if available (caller can set env)
    artifact = os.environ.get("NIGHT_SHIFT_REPORT_PATH")
    if artifact and Path(artifact).is_file():
        # Inject artifact as newest report body for compact render
        artifact_body = Path(artifact).read_text(encoding="utf-8", errors="replace").strip()
        text_for_render = artifact_body + "\n\n---\n\n" + text
    else:
        text_for_render = text

    new_text = render_rotated_log(
        text_for_render,
        product_id=project_dir.name,
        keep_full_reports=1,
    )

    if dry_run:
        return (
            f"dry-run {project_dir.name}: would archive {len(reports)} chunks "
            f"→ {archive_path.name}; keep latest PASS"
        )

    archive_dir.mkdir(parents=True, exist_ok=True)
    try:
        # Prefer group-writable archives (shared vault: secondbrain + operator)
        archive_dir.chmod(archive_dir.stat().st_mode | 0o2770)
    except OSError:
        pass
    try:
        archive_path.write_text(text, encoding="utf-8")
    except PermissionError as exc:
        return f"fail {project_dir.name}: cannot write archive {archive_path.name}: {exc}"
    try:
        log.write_text(new_text, encoding="utf-8")
    except PermissionError as exc:
        return f"fail {project_dir.name}: cannot rewrite log: {exc}"
    return (
        f"rotated {project_dir.name}: archived {len(reports)} reports "
        f"({len(fails)} FAIL / {len(passes)} PASS) → {archive_path.name}"
    )


def rebuild_multi_summary(vault: Path, *, dry_run: bool) -> str:
    """Rebuild 01-Projects/harness-night-shift/SUMMARY.md from each project's TODO."""
    projects = vault / "01-Projects"
    if not projects.is_dir():
        return "skip multi: no 01-Projects"
    rows: list[str] = []
    for d in sorted(projects.iterdir()):
        if not d.is_dir() or d.name in ("harness-night-shift",):
            continue
        todo = d / "TODO.md"
        log = d / "night-shift-log.md"
        overall = "?"
        when = "—"
        if todo.is_file():
            m = re.search(r"Overall:\s*\*\*(PASS|FAIL)\*\*", todo.read_text(encoding="utf-8", errors="replace"))
            if m:
                overall = m.group(1)
            m2 = re.search(r"at (\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC)", todo.read_text(encoding="utf-8", errors="replace"))
            if m2:
                when = m2.group(1)
        elif log.is_file():
            reps = _parse_reports(log.read_text(encoding="utf-8", errors="replace"))
            if reps:
                overall = reps[0]["overall"]
                when = reps[0]["when"]
        if overall == "?" and not todo.is_file() and not log.is_file():
            continue
        tag = "✅" if overall == "PASS" else ("❌" if overall == "FAIL" else "·")
        rows.append(f"| {d.name} | {tag} {overall} | {when} |")

    now = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        hkt = now.astimezone(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M HKT")
    except Exception:
        from datetime import timedelta
        hkt = now.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M HKT")
    when_s = f"{now.strftime('%Y-%m-%d %H:%M UTC')} · {hkt}"
    body = f"""# Multi-product night-shift summary

_Auto-rebuilt by `rotate_night_shift_logs.py` at {when_s}._

| Project | Latest | When |
|---------|--------|------|
{chr(10).join(rows) if rows else "| — | — | — |"}

## Ops

- Per-project detail: `01-Projects/<id>/TODO.md` + `night-shift-log.md`
- Rotate PASS noise: `python3 scripts/rotate_night_shift_logs.py --vault $PRODUCT_VAULT_ROOT`
- Full re-run: `python3 bin/night_shift_all_products.py`
"""
    out_dir = projects / "harness-night-shift"
    out = out_dir / "SUMMARY.md"
    if dry_run:
        return f"dry-run multi: would write {out} ({len(rows)} projects)"
    out_dir.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    return f"wrote multi SUMMARY ({len(rows)} projects) → {out}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    ap.add_argument("--only", action="append", default=[], help="Project folder name")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-multi", action="store_true", help="Skip harness-night-shift SUMMARY")
    args = ap.parse_args()
    vault = args.vault.expanduser().resolve()
    projects = vault / "01-Projects"
    if not projects.is_dir():
        print(f"❌ no 01-Projects under {vault}")
        return 1

    only = set(args.only) if args.only else None
    notes: list[str] = []
    for d in sorted(projects.iterdir()):
        if not d.is_dir():
            continue
        if d.name in ("harness-night-shift",):
            continue
        if only and d.name not in only:
            continue
        notes.append(rotate_project(d, dry_run=args.dry_run))

    if not args.no_multi:
        notes.append(rebuild_multi_summary(vault, dry_run=args.dry_run))

    for n in notes:
        print(n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
