#!/usr/bin/env python3
"""Tier B-3: content-address evidence pack files for PR_DRAFT / ship closeout.

  python3 scripts/evidence_hash.py --root .
  python3 scripts/evidence_hash.py --root . --write  # append table to PR_DRAFT
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

DEFAULT_PATHS = (
    ".agents/artifacts/CODE_REVIEW.md",
    ".agents/artifacts/CROSS_REVIEW.md",
    ".agents/artifacts/BEHAVIOR_REPORT.md",
    "PR_DRAFT.md",
    "VERSION",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def collect(root: Path, rels: list[str] | None = None) -> list[tuple[str, str | None]]:
    root = root.resolve()
    out: list[tuple[str, str | None]] = []
    for rel in rels or list(DEFAULT_PATHS):
        p = root / rel
        if p.is_file():
            out.append((rel, sha256_file(p)))
        else:
            out.append((rel, None))
    return out


def render_table(rows: list[tuple[str, str | None]]) -> str:
    lines = [
        "## Evidence hashes (Tier B-3)",
        "",
        "| Path | sha256 |",
        "|------|--------|",
    ]
    for rel, dig in rows:
        lines.append(f"| `{rel}` | `{dig or 'missing'}` |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--write", action="store_true", help="Append table to PR_DRAFT.md")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    rows = collect(root)
    table = render_table(rows)
    print(table)
    present = sum(1 for _, d in rows if d)
    if present == 0:
        print("⚠️  no evidence files present yet", file=sys.stderr)
        return 0
    if args.write:
        draft = root / "PR_DRAFT.md"
        prev = draft.read_text(encoding="utf-8") if draft.is_file() else "# PR draft\n"
        if "Evidence hashes (Tier B-3)" not in prev:
            draft.write_text(prev.rstrip() + "\n\n" + table, encoding="utf-8")
            print(f"✅ appended to {draft}")
        else:
            print("ok: evidence hash section already in PR_DRAFT")
    print(f"✅ evidence_hash: {present}/{len(rows)} files hashed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
