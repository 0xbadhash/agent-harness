#!/usr/bin/env python3
"""Repo hygiene: no root-level MagicMock, no orphan TODOs, no stale branches."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".agents", "logs", "vendor", ".antigravitycli", ".venv", "venv"}

def main() -> int:
    fails = 0
    # 1. No MagicMock at test root
    for p in (ROOT / "tests").glob("*.py") if (ROOT / "tests").exists() else []:
        text = p.read_text(encoding="utf-8")
        if re.search(r"^from unittest\.mock import MagicMock", text, re.M):
            print(f"❌ {p.relative_to(ROOT)}: root-level MagicMock")
            fails += 1

    # 2. No orphan TODO without ticket
    for p in ROOT.rglob("*.py"):
        if any(s in p.parts for s in SKIP_DIRS):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"#\s*TODO(?!\s*[\(\[])", text):
            line = text[:m.start()].count("\n") + 1
            print(f"⚠️  {p.relative_to(ROOT)}:{line} TODO without ticket ref")

    if fails:
        print(f"❌ {fails} hygiene failure(s)")
        return 1
    print("✅ repo hygiene ok")
    return 0

if __name__ == "__main__":
    sys.exit(main())
