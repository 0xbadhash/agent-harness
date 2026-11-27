#!/usr/bin/env python3
"""Suppression audit: every type suppression names a code, an owner, and an expiry.

A blanket suppression comment hides future errors as well as today's. The ban is
absolute: name the error code, the owner, and the date the suppression must be
gone. Expired suppressions fail.

Usage::

  python3 scripts/check_type_ignores.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore(?:\[([^\]]+)\])?")
ANNOTATION_RE = re.compile(
    r"owner=([A-Za-z0-9_.\-/]+).*?expires=(\d{4}-\d{2}-\d{2})"
)
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".agents",
}


def _files(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in Path(root).rglob("*.py"):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        out.append(p)
    return out


def scan_file(path: Path, root: Path, today: date) -> list[str]:
    findings: list[str] = []
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = str(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    for number, line in enumerate(text.splitlines(), 1):
        match = TYPE_IGNORE_RE.search(line)
        if not match:
            continue
        code = (match.group(1) or "").strip()
        if not code:
            findings.append(
                f"fail: {rel}:{number} blanket type-ignore needs [code] "
                "(owner and expires are also required)"
            )
            continue
        annotation = ANNOTATION_RE.search(line)
        if not annotation:
            findings.append(
                f"fail: {rel}:{number} type-ignore[{code}] missing "
                "`# owner=<ticket> expires=YYYY-MM-DD`"
            )
            continue
        expiry_raw = annotation.group(2)
        try:
            expiry = date.fromisoformat(expiry_raw)
        except ValueError:
            findings.append(f"fail: {rel}:{number} invalid expires date {expiry_raw}")
            continue
        if expiry < today:
            findings.append(
                f"fail: {rel}:{number} type-ignore[{code}] expired on {expiry_raw}"
            )
    return findings


def check(root: Path) -> tuple[bool, list[str]]:
    root = Path(root)
    today = datetime.now(UTC).date()
    findings: list[str] = []
    for path in _files(root):
        findings.extend(scan_file(path, root, today))
    if findings:
        return False, findings
    return True, ["type_ignores: every suppression is coded, owned, and current"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    ok, messages = check(args.root.resolve())
    for message in messages:
        print(("✅ " if ok else "❌ ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
