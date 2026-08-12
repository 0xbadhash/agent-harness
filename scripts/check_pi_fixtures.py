#!/usr/bin/env python3
"""Tier B-4: ensure prompt-injection fixtures exist and look like attacks (not empty)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

NEEDLES = ("ignore", "system", "secret", "token", "passwd", "exfil", "unrestricted")
REQUIRED = (
    "ignore_instructions.txt",
    "tool_exfil.txt",
    "role_hijack.txt",
)


def check(root: Path) -> tuple[bool, list[str]]:
    base = root / "fixtures" / "prompt_injection"
    msgs: list[str] = []
    if not base.is_dir():
        return False, [f"missing {base.relative_to(root)}"]
    for name in REQUIRED:
        p = base / name
        if not p.is_file():
            msgs.append(f"missing {name}")
            continue
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        if len(text.strip()) < 20:
            msgs.append(f"{name}: too short")
        elif not any(n in text for n in NEEDLES):
            msgs.append(f"{name}: does not look like PI fixture")
        else:
            msgs.append(f"ok: {name}")
    ok = not any(m.startswith("missing") or "too short" in m or "does not" in m for m in msgs)
    return ok, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    ok, msgs = check(args.root.resolve())
    for m in msgs:
        print(("✅ " if m.startswith("ok:") else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
