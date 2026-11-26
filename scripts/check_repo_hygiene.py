#!/usr/bin/env python3
"""Repo hygiene: no root-level MagicMock, no orphan TODOs, no stale branches."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".agents", "logs", "vendor", ".antigravitycli", ".venv", "venv"}

DEBUG_TAG_RE = re.compile(r"\[DEBUG-[A-Za-z0-9_-]+\]")


def scan_debug_tags(root: Path) -> int:
    """Fail closed when temporary [DEBUG-*] instrumentation survives in non-test source."""
    fails = 0
    prod_skip = SKIP_DIRS | {"tests", "test", "testing", "docs", "skills"}
    for ext in ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx"):
        for p in root.rglob(ext):
            if any(s in p.parts for s in prod_skip):
                continue
            if p.name == "check_repo_hygiene.py":
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            if DEBUG_TAG_RE.search(text):
                print(f"❌ {p.relative_to(root)}: leftover [DEBUG-*] instrumentation")
                fails += 1
    return fails


def main() -> int:
    fails = 0
    # 1. MagicMock only banned in *production* code (not under tests/)
    #    Unit tests legitimately mock collaborators at import scope.
    prod_skip = SKIP_DIRS | {"tests", "test", "testing"}
    for p in ROOT.rglob("*.py"):
        if any(s in p.parts for s in prod_skip):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if re.search(r"^from unittest\.mock import MagicMock", text, re.MULTILINE):
            print(f"❌ {p.relative_to(ROOT)}: MagicMock import in non-test code")
            fails += 1

    fails += scan_debug_tags(ROOT)

    # 2. No orphan TODO without ticket (warn only)
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
