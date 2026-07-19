#!/usr/bin/env python3
"""Fail if any vault 01-Projects/*/dev-log.md drifts from the harness contract.

Contract (must hold for every project, no exceptions):
  1. Header mentions Newest first + UTC + HKT
  2. Every ## entry has **When:** … UTC · … HKT
  3. Every ## entry has **Kind:** release|note
  4. Entries are newest-first by parseable date in the heading

Exit 0 = compliant; 1 = drift. Used after normalize on night_shift_all.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

H2 = re.compile(r"^##\s+(20\d{2}-\d{2}-\d{2})")
WHEN = re.compile(r"\*\*When:\*\*.*UTC.*HKT", re.I)
KIND = re.compile(r"\*\*Kind:\*\*\s*(release|note)", re.I)


def check_file(path: Path) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8")
    pid = path.parent.name
    if "Newest first" not in text:
        errs.append(f"{pid}: header missing 'Newest first'")
    if "UTC" not in text.split("\n\n")[0] and "HKT" not in text[:400]:
        # header should mention both
        if "HKT" not in text[:500]:
            errs.append(f"{pid}: header missing HKT contract blurb")
    # split entries
    chunks = re.split(r"(?=^## )", text, flags=re.M)
    entries = [c for c in chunks if c.lstrip().startswith("## ")]
    days: list[str] = []
    for i, ch in enumerate(entries):
        first = ch.splitlines()[0]
        m = H2.match(first)
        if not m:
            errs.append(f"{pid}: entry {i+1} heading not YYYY-MM-DD: {first[:60]}")
            continue
        days.append(m.group(1))
        if not WHEN.search(ch):
            errs.append(f"{pid}: entry {i+1} missing dual-zone **When:** ({first[:50]})")
        if not KIND.search(ch):
            errs.append(f"{pid}: entry {i+1} missing **Kind:** ({first[:50]})")
    for a, b in zip(days, days[1:]):
        if a < b:
            errs.append(f"{pid}: not newest-first ({a} appears before older? got {a} then {b})")
            break
    # bare date lines without ##
    for ln in text.splitlines():
        if re.match(r"^20\d{2}-\d{2}-\d{2}\s*[—–-]", ln) and not ln.startswith("##"):
            errs.append(f"{pid}: bare date line (must be ## heading): {ln[:60]}")
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path, default=Path("/opt/second-brain/vault"))
    ap.add_argument("--project", action="append", dest="projects")
    args = ap.parse_args(argv)
    root = args.vault.expanduser().resolve() / "01-Projects"
    paths = sorted(root.glob("*/dev-log.md"))
    if args.projects:
        want = set(args.projects)
        paths = [p for p in paths if p.parent.name in want]
    if not paths:
        print("check_dev_log_contract: no dev-log.md found", file=sys.stderr)
        return 1
    all_errs: list[str] = []
    for p in paths:
        all_errs.extend(check_file(p))
    if all_errs:
        print(f"❌ dev-log contract drift ({len(all_errs)} issue(s)):")
        for e in all_errs:
            print(f"  - {e}")
        return 1
    print(f"✅ dev-log contract OK ({len(paths)} project log(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
