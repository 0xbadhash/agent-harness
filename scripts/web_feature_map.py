#!/usr/bin/env python3
"""Print a feature map from the web E2E contract. Default is stdout."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from web_e2e_contract import allocate_scenario_ids, validate_web_e2e  # noqa: E402


def map_rows(root: Path) -> list[tuple[str, str, str, str]]:
    report = validate_web_e2e(root)
    scenarios = list(report.get("scenarios") or [])
    if not scenarios:
        scenarios = allocate_scenario_ids([])
    rows: list[tuple[str, str, str, str]] = []
    for sc in scenarios:
        rows.append(
            (
                str(sc.get("global_id") or ""),
                str(sc.get("surface_id") or ""),
                str(sc.get("path") or ""),
                str(sc.get("name") or ""),
            )
        )
    return rows


def render(rows: list[tuple[str, str, str, str]]) -> str:
    lines = [
        "| S-id | surface | path | proves |",
        "|------|---------|------|--------|",
    ]
    for sid, surface, path, proves in rows:
        lines.append(f"| {sid} | {surface} | {path} | {proves} |")
    if not rows:
        lines.append("| — | — | — | — |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    text = render(map_rows(args.root.expanduser().resolve()))
    if args.out is None:
        sys.stdout.write(text)
    else:
        dest = args.out.expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
