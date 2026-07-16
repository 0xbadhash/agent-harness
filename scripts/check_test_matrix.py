#!/usr/bin/env python3
"""Verify product test matrix paths exist (test presence, not pass/fail)."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MATRIX = ROOT / ".agents" / "policy" / "TEST_MATRIX.md"


def parse_matrix(path: Path) -> list[dict]:
    """Parse markdown table rows from TEST_MATRIX.md."""
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        rid = cells[0]
        if rid.lower() == "id" or re.match(r"^[-:\s]+$", rid):
            continue
        surface = cells[1]
        must = cells[2]
        if "must_exist" in must.lower():
            continue
        paths = [p.strip() for p in must.split(",") if p.strip()]
        if not paths:
            continue
        out.append({"id": rid, "surface": surface, "paths": paths})
    return out


def check_matrix(root: Path, matrix_path: Path) -> tuple[bool, list[dict]]:
    rows = parse_matrix(matrix_path)
    results: list[dict] = []
    ok_all = True
    for row in rows:
        missing = [p for p in row["paths"] if not (root / p).exists()]
        present = [p for p in row["paths"] if (root / p).exists()]
        ok = not missing
        if not ok:
            ok_all = False
        results.append(
            {
                "id": row["id"],
                "surface": row["surface"],
                "ok": ok,
                "present": present,
                "missing": missing,
            }
        )
    return ok_all, results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    ok, results = check_matrix(args.root, args.matrix)
    if args.json:
        print(json.dumps({"pass": ok, "rows": results}, indent=2))
    else:
        for r in results:
            tag = "✅" if r["ok"] else "❌"
            print(f"{tag} {r['id']}: {r['surface']}")
            for m in r["missing"]:
                print(f"   missing: {m}")
        fails = sum(1 for r in results if not r["ok"])
        print("✅ test matrix ok" if ok else f"❌ test matrix failed ({fails} rows)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
