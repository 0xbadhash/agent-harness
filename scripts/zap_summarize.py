#!/usr/bin/env python3
"""Summarize ZAP HTML/log artifacts into a short markdown (no raw HTML in ops loops)."""
from __future__ import annotations

import argparse
import re
from datetime import UTC, datetime
from pathlib import Path


def summarize(report_dir: Path) -> str:
    lines = [
        "# ZAP baseline summary",
        "",
        f"_Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} by zap_summarize.py_",
        "",
        "| Target log | High|Med|Low|Info (approx from log) | HTML size |",
        "|------------|---------------------------|-----------|",
    ]
    logs = sorted(report_dir.glob("zap-*.log"))
    if not logs:
        lines.append("| — | no zap-*.log | — |")
    for log in logs:
        text = log.read_text(encoding="utf-8", errors="replace")
        # ZAP baseline often prints WARN-NEW / FAIL-NEW counts
        highs = len(re.findall(r"FAIL-NEW|High\b", text, re.I))
        meds = len(re.findall(r"WARN-NEW|Medium\b", text, re.I))
        html = log.with_suffix(".html")
        # name pattern zap-https___host.html
        hsize = html.stat().st_size if html.is_file() else 0
        lines.append(
            f"| `{log.name}` | ~H{highs}/M{meds} (keyword hits) | {hsize} B |"
        )
    lines.extend(
        [
            "",
            "> Raw HTML stays under `.agents/artifacts/zap/` for manual triage — "
            "**do not** paste HTML into night/ship reports.",
            "> ZAP is **not** part of night_shift_all (schedule / manual only).",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dir",
        type=Path,
        default=Path(".agents/artifacts/zap"),
    )
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    d = args.dir
    if not d.is_dir():
        print(f"⚠️  no report dir {d}")
        return 0
    md = summarize(d)
    print(md)
    if args.write:
        out = d / "SUMMARY.md"
        out.write_text(md, encoding="utf-8")
        print(f"✅ wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
