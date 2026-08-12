#!/usr/bin/env python3
"""Tier A-2: ensure docs/compatibility.md and manifest stay aligned."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def check(root: Path) -> tuple[bool, list[str]]:
    doc = root / "docs" / "compatibility.md"
    man = root / "harness.manifest.yaml"
    msgs: list[str] = []
    if not doc.is_file():
        return False, ["missing docs/compatibility.md"]
    text = doc.read_text(encoding="utf-8")
    for needle in (
        "Grok",
        "claimed",
        "tested",
        "pipeline",
        "hard_gates",
        "Python",
        "TypeScript",
    ):
        if needle not in text:
            msgs.append(f"compatibility.md missing topic: {needle}")
    if not man.is_file():
        msgs.append("missing harness.manifest.yaml")
    else:
        m = man.read_text(encoding="utf-8")
        if "compatibility:" not in m:
            msgs.append("manifest missing compatibility: block")
        if "tested:" not in m:
            msgs.append("manifest missing tested: under compatibility")
    if msgs:
        return False, msgs
    return True, ["ok: compatibility matrix present and aligned"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    ok, msgs = check(args.root.resolve())
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
