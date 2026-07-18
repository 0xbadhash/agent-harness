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
from datetime import datetime, timezone
from pathlib import Path

_HOME = Path.home()
DEFAULT_VAULT = Path(
    os.environ.get("PRODUCT_VAULT_ROOT")
    or os.environ.get("WATCHLIST_VAULT_ROOT")
    or "/opt/second-brain/vault"
)

OVERALL_RE = re.compile(
    r"^\*\*Overall:\*\*\s*(PASS|FAIL)\b.*$",
    re.M,
)
HEADER_RE = re.compile(
    r"^# Night shift readiness — (\S+) — (.+)$",
    re.M,
)


def _parse_reports(text: str) -> list[dict]:
    """Split append-only log into report chunks."""
    parts = re.split(r"(?=^# Night shift readiness — )", text, flags=re.M)
    out: list[dict] = []
    for part in parts:
        part = part.strip()
        if not part.startswith("# Night shift readiness"):
            continue
        hm = HEADER_RE.search(part)
        om = OVERALL_RE.search(part)
        out.append(
            {
                "product": hm.group(1) if hm else "?",
                "when": hm.group(2).strip() if hm else "?",
                "overall": om.group(1) if om else "?",
                "body": part,
            }
        )
    return out


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
    latest_body = latest["body"]
    if artifact and Path(artifact).is_file():
        latest_body = Path(artifact).read_text(encoding="utf-8", errors="replace").strip()

    # Compact timeline from parsed history
    rows = []
    for r in reports:
        rows.append(f"| {r['when']} | {r['overall']} |")
    table = "\n".join(rows) if rows else "| — | — |"

    new_text = f"""# {project_dir.name} night-shift log

Append-only readiness reports from `/night_shift` (harness SoT).

## How to read

- **Latest status wins** for ops.
- Full raw history archived under `_archive/` when rotated after a PASS.

## Timeline (auto-rotated {when})

| When | Result |
|------|--------|
{table}

---

{latest_body}
"""

    if dry_run:
        return (
            f"dry-run {project_dir.name}: would archive {len(reports)} chunks "
            f"→ {archive_path.name}; keep latest PASS"
        )

    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(text, encoding="utf-8")
    log.write_text(new_text, encoding="utf-8")
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
