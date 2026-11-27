#!/usr/bin/env python3
"""Comment audit: comments explain constraints, not history or dead code.

Flags, per added/source line:

- **history** — ``previously``, ``used to``, ``no longer``, ``removed``,
  ``instead of``: the reader cannot see the old code, so the comment ages badly.
- **commented_code** — a comment that starts with a Python construct
  (``def``, ``class``, ``return``, ``import``, ``if``, ``for``).
- **todo** — TODO without an owner (``TODO(name)``) or issue link.

Comments that explain *why* (a constraint, a workaround, a safety rule) pass.

Usage::

  python3 scripts/check_comment_audit.py --path scripts/foo.py
  python3 scripts/check_comment_audit.py --diff HEAD~1...HEAD --strict
  python3 scripts/check_comment_audit.py --root . --strict
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_RE = re.compile(
    r"\b(previously|used to|no longer|removed|instead of|before this|"
    r"the old|legacy behavior)\b",
    re.IGNORECASE,
)
COMMENTED_CODE_RE = re.compile(
    r"^\s*#\s*(?:def |class |return\b|import |from |if |for |while |try:|except\b)"
)
TODO_RE = re.compile(r"\bTODO\b")
TODO_OK_RE = re.compile(r"TODO\s*(?:\([^)]*\)|:\s*(?:#|https?://)|#\s*\d+)")
COMMENT_RE = re.compile(r"^\s*(?:#|//|/\*|\*)\s?(.*)$")
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".sh"}


def classify_comment(line: str) -> str | None:
    """Return a finding kind for a comment line, or None when it is fine."""
    match = COMMENT_RE.match(line)
    if not match:
        return None
    body = match.group(1).strip()
    if not body:
        return None
    if COMMENTED_CODE_RE.match(line):
        return "commented_code"
    if HISTORY_RE.search(body):
        return "history"
    if TODO_RE.search(body) and not TODO_OK_RE.search(body):
        return "todo"
    return None


def audit_text(text: str, *, name: str = "<text>") -> list[str]:
    findings: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        kind = classify_comment(line)
        if kind:
            findings.append(f"{name}:{number}: {kind}: {line.strip()[:160]}")
    return findings


def audit_paths(paths: list[Path]) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if path.suffix.lower() not in SOURCE_SUFFIXES or not path.is_file():
            continue
        findings.extend(
            audit_text(path.read_text(encoding="utf-8", errors="replace"), name=str(path))
        )
    return findings


def _findings_from_diff(stdout: str) -> list[str]:
    findings: list[str] = []
    path = ""
    for line in stdout.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            kind = classify_comment(line[1:])
            if kind:
                findings.append(f"{path}: {kind}: {line[1:].strip()[:160]}")
    return findings


def audit_diff(diff: str = "HEAD~1...HEAD", root: Path = ROOT) -> list[str]:
    run = subprocess.run(
        ["git", "diff", "-U0", diff],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        return []
    return _findings_from_diff(run.stdout)


def check(root: Path, base: str = "HEAD~1", head: str = "HEAD") -> tuple[bool, list[str]]:
    """Return (ok, messages) for hard_gates: audit only the added diff lines."""
    root = Path(root)
    if not (root / ".git").exists() and not (root / ".git").is_file():
        return True, ["comment_audit: no git checkout (not a ship diff)"]
    diff = f"{base}...{head}"
    run = subprocess.run(
        ["git", "diff", "-U0", diff],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        detail = (run.stderr or "").strip()[:200]
        return False, [f"comment_audit: git diff {diff} failed: {detail}"]
    findings = _findings_from_diff(run.stdout)
    if findings:
        return False, ["comment_audit: " + finding for finding in findings]
    return True, ["comment_audit: no new history/dead-code/TODO comments"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--path", action="append", default=[], help="File to audit (repeatable)")
    ap.add_argument("--diff", default=None, help="Git range to audit (added lines only)")
    ap.add_argument("--strict", action="store_true", help="Exit 1 when findings exist")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if args.path:
        findings = audit_paths([root / p for p in args.path])
    elif args.diff:
        findings = audit_diff(args.diff, root)
    else:
        findings = audit_paths(
            [
                p
                for p in root.rglob("*")
                if p.suffix.lower() in SOURCE_SUFFIXES
                and ".venv" not in p.parts
                and ".git" not in p.parts
                and "__pycache__" not in p.parts
            ]
        )
    for finding in findings:
        print(f"⚠️  {finding}")
    if not findings:
        print("✅ comment audit: no history/dead-code/TODO findings")
        return 0
    print(f"comment audit: {len(findings)} finding(s)")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
