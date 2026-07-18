#!/usr/bin/env python3
"""Canonical vault night-shift-log.md template (Timeline + dual UTC/HKT + newest-first).

Shared by night_shift_readiness (prepend) and rotate_night_shift_logs (compact).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

READINESS_HEADER_RE = re.compile(
    r"^# Night shift readiness — (\S+) — (.+)$",
    re.M,
)
OVERALL_RE = re.compile(
    r"^\*\*Overall:\*\*\s*(PASS|FAIL)\b",
    re.M,
)
TIMELINE_ROW_RE = re.compile(
    r"^\|\s*(.+?)\s*\|\s*(PASS|FAIL)\s*\|\s*$",
    re.M,
)


def format_when_dual(when: datetime | None = None) -> str:
    """UTC + Asia/Hong_Kong wall times for operators."""
    when = when or datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    else:
        when = when.astimezone(timezone.utc)
    utc_s = when.strftime("%Y-%m-%d %H:%M UTC")
    try:
        from zoneinfo import ZoneInfo

        hkt = when.astimezone(ZoneInfo("Asia/Hong_Kong"))
        hkt_s = hkt.strftime("%Y-%m-%d %H:%M HKT")
    except Exception:  # noqa: BLE001
        hkt = when.astimezone(timezone(timedelta(hours=8)))
        hkt_s = hkt.strftime("%Y-%m-%d %H:%M HKT")
    return f"{utc_s} · {hkt_s}"


def parse_reports(text: str) -> list[dict[str, str]]:
    """Split log into readiness report chunks (document order = newest-first when well-formed)."""
    parts = re.split(r"(?=^# Night shift readiness — )", text, flags=re.M)
    out: list[dict[str, str]] = []
    for part in parts:
        part = part.strip()
        if not part.startswith("# Night shift readiness"):
            continue
        hm = READINESS_HEADER_RE.search(part)
        om = OVERALL_RE.search(part)
        out.append(
            {
                "product": hm.group(1) if hm else "?",
                "when": hm.group(2).strip() if hm else "?",
                "overall": om.group(1) if om else "?",
                "body": part.rstrip() + "\n",
            }
        )
    return out


def parse_timeline_rows(text: str) -> list[tuple[str, str]]:
    """Extract Timeline table rows if present (When, Result)."""
    # Horizontal rule after Timeline is a line that is only --- (not table cells)
    m = re.search(
        r"## Timeline\s*\n(.*?)(?:\n---\s*\n|\n# Night shift readiness)",
        text,
        re.S,
    )
    if not m:
        return []
    block = m.group(1)
    rows: list[tuple[str, str]] = []
    for rm in TIMELINE_ROW_RE.finditer(block):
        when = rm.group(1).strip()
        if when.lower() == "when" or set(when) <= {"-", " "}:
            continue
        rows.append((when, rm.group(2)))
    return rows


def _timeline_from_reports(reports: list[dict[str, str]]) -> list[tuple[str, str]]:
    return [(r["when"], r["overall"]) for r in reports if r.get("when") and r.get("overall") in ("PASS", "FAIL")]


def merge_timeline(
    existing_rows: list[tuple[str, str]],
    new_when: str,
    new_overall: str,
) -> list[tuple[str, str]]:
    """Newest-first; drop duplicate exact (when, result) then prepend new."""
    rows = [(new_when, new_overall)]
    for when, overall in existing_rows:
        if when == new_when and overall == new_overall:
            continue
        rows.append((when, overall))
    return rows


def render_log_document(
    product_id: str,
    timeline: list[tuple[str, str]],
    report_bodies: list[str],
) -> str:
    """Canonical night-shift-log.md body."""
    lines = [
        f"# {product_id} night-shift log",
        "",
        "Newest-first readiness reports (`/night_shift` harness SoT).",
        "Each entry: **UTC · HKT**. Hard-stops: no release, no push, no product auto-fix.",
        "",
        "## Timeline",
        "",
        "| When | Result |",
        "| --- | --- |",
    ]
    for when, overall in timeline:
        lines.append(f"| {when} | {overall} |")
    if not timeline:
        lines.append("| — | — |")
    lines.append("")
    lines.append("---")
    lines.append("")
    bodies: list[str] = []
    for body in report_bodies:
        b = body.strip()
        if b:
            bodies.append(b)
    lines.append("\n\n---\n\n".join(bodies))
    if bodies:
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_night_shift_log(
    log_path: Path,
    *,
    product_id: str,
    report_md: str,
    overall: str | None = None,
    when_label: str | None = None,
) -> None:
    """Write/update log: Timeline + full reports newest-first (prepend semantics)."""
    if overall:
        overall = overall.upper()
    if not overall or overall not in ("PASS", "FAIL"):
        om = OVERALL_RE.search(report_md)
        overall = om.group(1) if om else "FAIL"

    when_label = when_label or ""
    if not when_label:
        hm = READINESS_HEADER_RE.search(report_md)
        when_label = hm.group(2).strip() if hm else format_when_dual()

    existing = ""
    if log_path.is_file():
        existing = log_path.read_text(encoding="utf-8", errors="replace")

    prior_reports = parse_reports(existing)
    # Prefer report-derived timeline order; fall back to existing Timeline table
    prior_rows = _timeline_from_reports(prior_reports)
    if not prior_rows:
        prior_rows = parse_timeline_rows(existing)

    timeline = merge_timeline(prior_rows, when_label, overall)
    new_body = report_md.rstrip() + "\n"
    bodies = [new_body] + [r["body"] for r in prior_reports]
    text = render_log_document(product_id, timeline, bodies)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(text, encoding="utf-8")


def render_rotated_log(
    existing_text: str,
    *,
    product_id: str,
    keep_full_reports: int = 1,
) -> str:
    """Compact after PASS rotate: full Timeline history + N newest full reports."""
    reports = parse_reports(existing_text)
    rows = _timeline_from_reports(reports)
    if not rows:
        rows = parse_timeline_rows(existing_text)
    bodies = [r["body"] for r in reports[: max(0, keep_full_reports)]]
    return render_log_document(product_id, rows, bodies)


# Back-compat alias used by older call sites
prepend_night_shift_log = write_night_shift_log
