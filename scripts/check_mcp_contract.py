#!/usr/bin/env python3
"""Tier B-1: optional product_plugin mcp block is well-formed (warn-only default)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def check(root: Path, *, strict: bool = False) -> tuple[bool, list[str]]:
    root = root.resolve()
    plugin = root / "product_plugin.yaml"
    msgs: list[str] = []
    if not plugin.is_file():
        return True, ["ok: no product_plugin.yaml (mcp N/A)"]
    text = plugin.read_text(encoding="utf-8", errors="replace")
    if "mcp:" not in text:
        return True, ["ok: no mcp: block (optional)"]
    # Minimal structure checks without requiring PyYAML
    if "required:" not in text and "documented:" not in text:
        msgs.append("mcp: present but missing required: or documented: keys")
    else:
        msgs.append("ok: mcp block present")
    if msgs and any(m.startswith("mcp:") for m in msgs):
        return (not strict), msgs
    return True, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    ok, msgs = check(args.root.resolve(), strict=bool(args.strict))
    for m in msgs:
        print(("✅ " if ok else ("❌ " if args.strict else "⚠️  ")) + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
