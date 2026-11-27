#!/usr/bin/env python3
"""Comment audit: comments explain constraints, not history or escape hatches.

Flags, per added/source line:

- **history** — ``previously``, ``used to``, ``no longer``, ``removed``,
  ``instead of``: the reader cannot see the old code, so the comment ages badly.
- **commented_code** — a comment that starts with a Python construct
  (``def``, ``class``, ``return``, ``import``, ``if``, ``for``).
- **todo** — TODO without an owner (``TODO(name)``) or issue link.
- **escape_hatch** — ``for now``, ``temporary``, ``works around``,
  ``safe to ignore``: a justification for skipping the check unless the comment
  names the check that bounds it (``scripts/…``, ``tests/…``, ``check:_``).

Comments that explain *why* (a constraint, a workaround with an owner, a safety
rule) pass.

``--baseline`` ratchets whole-tree runs: findings may fall, never rise above the
recorded per-``path::kind`` counts. ``--update-baseline`` records the floor.

Usage::

  python3 scripts/check_comment_audit.py --path scripts/foo.py
  python3 scripts/check_comment_audit.py --diff HEAD~1...HEAD --strict
  python3 scripts/check_comment_audit.py --root . --baseline config/comment_audit_baseline.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_RE = re.compile(
    r"\b(previously|used to|no longer|removed|instead of|before this|"
    r"the old|legacy behavior)\b",
    re.IGNORECASE,
)
JUSTIFY_RE = re.compile(
    r"\b(for now|temporar(?:y|ily)|works? around|safe to ignore|just in case)\b",
    re.IGNORECASE,
)
CHECK_REF_RE = re.compile(
    r"(scripts/[\w./-]+|tests?/[\w./-]+|check[:_-]|/pr_review|next_skill)",
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
    if JUSTIFY_RE.search(body) and not CHECK_REF_RE.search(body):
        return "escape_hatch"
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


def _source_paths(root: Path, paths: list[Path]) -> list[Path]:
    return [
        p
        for p in paths
        if p.suffix.lower() in SOURCE_SUFFIXES and p.is_file()
    ]


def audit_paths(paths: list[Path], *, root: Path | None = None) -> list[str]:
    findings: list[str] = []
    for path in paths:
        if path.suffix.lower() not in SOURCE_SUFFIXES or not path.is_file():
            continue
        name = str(path)
        if root is not None:
            try:
                name = path.relative_to(root).as_posix()
            except ValueError:
                name = str(path)
        findings.extend(
            audit_text(path.read_text(encoding="utf-8", errors="replace"), name=name)
        )
    return findings


def _finding_rows(root: Path, paths: list[Path]) -> list[tuple[str, str, str]]:
    """Return (relpath, kind, formatted-finding) tuples."""
    rows: list[tuple[str, str, str]] = []
    for path in _source_paths(root, paths):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = str(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            kind = classify_comment(line)
            if kind:
                rows.append(
                    (rel, kind, f"{rel}:{number}: {kind}: {line.strip()[:160]}")
                )
    return rows


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


def _load_baseline(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): int(v) for k, v in data.items()}


def _count_keys(rows: list[tuple[str, str, str]]) -> dict[str, int]:
    return dict(Counter(f"{rel}::{kind}" for rel, kind, _ in rows))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--path", action="append", default=[], help="File to audit (repeatable)")
    ap.add_argument("--diff", default=None, help="Git range to audit (added lines only)")
    ap.add_argument("--strict", action="store_true", help="Exit 1 when findings exist")
    ap.add_argument("--baseline", type=Path, default=None, help="Ratchet counts JSON")
    ap.add_argument(
        "--update-baseline", action="store_true", help="Write current counts as the floor"
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()

    if args.path or args.diff:
        if args.path:
            findings = audit_paths([root / p for p in args.path], root=root)
        else:
            findings = audit_diff(args.diff, root)
        for finding in findings:
            print(f"⚠️  {finding}")
        if not findings:
            print("✅ comment audit: no history/dead-code/TODO findings")
            return 0
        print(f"comment audit: {len(findings)} finding(s)")
        return 1 if args.strict else 0

    paths = [
        p
        for p in root.rglob("*")
        if p.suffix.lower() in SOURCE_SUFFIXES
        and ".venv" not in p.parts
        and ".git" not in p.parts
        and "__pycache__" not in p.parts
    ]
    rows = _finding_rows(root, paths)
    counts = _count_keys(rows)

    if args.update_baseline:
        if args.baseline is None:
            print("❌ --update-baseline needs --baseline", file=sys.stderr)
            return 1
        args.baseline.write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
        print(f"✅ comment-audit baseline updated: {args.baseline} ({sum(counts.values())} findings)")
        return 0

    if args.baseline is not None:
        baseline = _load_baseline(args.baseline)
        excess = {
            key: value
            for key, value in counts.items()
            if value > int(baseline.get(key, 0))
        }
        for key, value in sorted(excess.items()):
            print(f"⚠️  {key}: {value} > {int(baseline.get(key, 0))}")
        if not excess:
            print(f"✅ comment audit: {sum(counts.values())} known, no increase")
            return 0
        print(f"comment audit: {len(excess)} key(s) above baseline")
        return 1

    for _, _, finding in rows:
        print(f"⚠️  {finding}")
    if not rows:
        print("✅ comment audit: no history/dead-code/TODO findings")
        return 0
    print(f"comment audit: {len(rows)} finding(s)")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
