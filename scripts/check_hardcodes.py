#!/usr/bin/env python3
"""Scans source for hardcoded paths/URLs/credentials. Zero tolerance."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".agents",
    "logs",
    "vendor",
    ".antigravitycli",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "infra",
    "cache",
    "var",
    # Local Graphify code maps (gitignored; absolute paths + false-positive digit keys)
    "graphify-out",
    # Portable skill markdown often cites external docs URLs
    "skills",
    # Sample configs / fixtures (product-specific paths)
    "examples",
}
SKIP_FILES = {
    "ALL_PRINCIPLES.md",
    "PRODUCTION_GAP_ANALYSIS.md",
    "README.md",
    "CHANGELOG.md",
    "DEPLOYMENT_GUIDE.md",
    "BACKEND_ROADMAP.md",
    "RELEASE_RUNBOOK.md",
    "PR_DRAFT.md",
    "WORKFLOW_DOCUMENTATION.md",
}

PATTERNS = [
    (re.compile(r"/home/[a-z]+", re.I), "absolute_user_path"),
    (re.compile(r"C:\\\\Users\\\\", re.I), "windows_user_path"),
    (re.compile(r"(?<![_\w])(password|secret|api_key|token)\s*=\s*['\"][^'\"]{6,}['\"]", re.I), "inline_secret"),
    (re.compile(r"https?://(?!localhost|127\.0\.0\.1|example\.com)[\w.-]+\.\w{2,}", re.I), "external_url"),
    (re.compile(r"\b[A-Z0-9]{16}\b"), "exposed_api_key"),
]

# Allow-list: config defaults, tests, deploy units (host paths)
ALLOW = [
    "config/settings.py",
    "tests/",
    "test_",
    "conftest.py",
    "migration/deploy/",
    "deploy/",
    "docs/",
]

def main() -> int:
    hits = 0
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(s in p.parts for s in SKIP_DIRS):
            continue
        if p.name in SKIP_FILES:
            continue
        if p.suffix not in {".py", ".md", ".json", ".yaml", ".yml", ".toml"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = p.relative_to(ROOT)
        if any(a in str(rel) for a in ALLOW):
            continue
        for rx, tag in PATTERNS:
            for m in rx.finditer(text):
                line = text[:m.start()].count("\n") + 1
                print(f"❌ {rel}:{line} [{tag}] {m.group(0)[:60]}")
                hits += 1
    if hits:
        print(f"❌ {hits} hardcode violation(s)")
        return 1
    print("✅ no hardcodes")
    return 0

if __name__ == "__main__":
    sys.exit(main())
