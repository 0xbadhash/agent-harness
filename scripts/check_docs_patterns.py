#!/usr/bin/env python3
"""Fail when docs or skills teach a rejected harness pattern.

Patterns live in ``.agents/policy/rejected-patterns.md``. The scan covers
``docs/`` (excluding ``docs/specs/``), ``skills/``, ``templates/``, ``README.md``,
and ``AGENTS.md``. A line that names the pattern as retired, removed, forbidden,
or replaced is allowed; add ``<!-- pattern-ok -->`` for a deliberate exception.

Usage::

  python3 scripts/check_docs_patterns.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERNS = (
    ("yolo-flag", re.compile(r"--yolo\b"), "run the phase FSM instead"),
    (
        "retired-interview-flags",
        re.compile(r"--no-(?:interview|clarify)\b"),
        "use --spike with a recorded reason",
    ),
    (
        "direct-main-push",
        re.compile(r"git\s+push\s+(?:origin\s+)?main\b"),
        "open a branch and a PR",
    ),
    (
        "bare-type-ignore",
        re.compile(r"#\s*type:\s*ignore\s*$"),
        "use a specific error code or fix the type",
    ),
)
NEGATIVE_RE = re.compile(
    r"\b(retired|rejected|removed|ignored|not available|forbidden|never|"
    r"do not|don't|instead|blocked|protected)\b",
    re.IGNORECASE,
)
ALLOW_MARKER = "pattern-ok"
SCAN_DIRS = ("docs", "skills", "templates")
ROOT_FILES = ("README.md", "AGENTS.md")


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = [root / name for name in ROOT_FILES if (root / name).is_file()]
    for area in SCAN_DIRS:
        base = root / area
        if not base.is_dir():
            continue
        for path in base.rglob("*.md"):
            if "specs" in path.relative_to(root).parts:
                continue
            files.append(path)
    return files


def check(root: Path) -> tuple[bool, list[str]]:
    """Return (ok, findings)."""
    root = Path(root)
    failures: list[str] = []
    for path in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if ALLOW_MARKER in line or NEGATIVE_RE.search(line):
                continue
            for name, rx, fix in PATTERNS:
                if rx.search(line):
                    failures.append(
                        f"{rel}:{number}: {name} — {line.strip()[:120]} (use {fix})"
                    )
    return (not failures), failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    ok, findings = check(args.root)
    if ok:
        print("✅ no rejected patterns taught in docs or skills")
        return 0
    for finding in findings:
        print(f"❌ {finding}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
