#!/usr/bin/env python3
"""Roll up NIGHT_SHIFT_REPORT.md failure gates across products (C3)."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

GATE_FAIL = re.compile(r"^\|\s*`?([a-zA-Z0-9_]+)`?\s*\|\s*❌", re.M)
OVERALL = re.compile(r"\*\*Overall:\*\*\s*(FAIL|PASS)", re.I)


def scan_report(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return GATE_FAIL.findall(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--roots",
        nargs="*",
        default=[],
        help="Product roots (default: scan ~/ for .agents/artifacts/NIGHT_SHIFT_REPORT.md)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path(".agents/artifacts/NIGHT_SHIFT_TAXONOMY.md"),
    )
    args = ap.parse_args(argv)

    reports: list[Path] = []
    if args.roots:
        for r in args.roots:
            p = Path(r).expanduser() / ".agents" / "artifacts" / "NIGHT_SHIFT_REPORT.md"
            if p.is_file():
                reports.append(p)
    else:
        home = Path.home()
        for p in home.glob("*/.agents/artifacts/NIGHT_SHIFT_REPORT.md"):
            reports.append(p)

    counts: Counter[str] = Counter()
    per_product: list[str] = []
    for rep in sorted(reports):
        product = rep.parts[-4] if len(rep.parts) >= 4 else str(rep)
        fails = scan_report(rep)
        for g in fails:
            counts[g] += 1
        per_product.append(f"- **{product}**: {', '.join(fails) if fails else '(no ❌ gates parsed)'}")

    lines = [
        "# Night-shift failure taxonomy",
        "",
        f"Reports scanned: {len(reports)}",
        "",
        "## Gate frequency",
        "",
    ]
    if not counts:
        lines.append("_No gate failures parsed._")
    else:
        for gate, n in counts.most_common():
            lines.append(f"- `{gate}`: {n}")
    lines.extend(["", "## Per product", ""] + per_product + [""])

    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
