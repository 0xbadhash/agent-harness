#!/usr/bin/env python3
"""Repo hygiene: scratch artifacts, dirty tree, MagicMock, orphan TODOs."""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
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
}
SCRATCH_PATTERNS = (
    "*.bak-*",
    "*.orig",
    "*.rej",
    ".coverage",
    ".coverage.*",
    ".venv-*bak*",
    "signal-cli-canary-*",
)


def scan_scratch_artifacts(root: Path) -> list[str]:
    """Return repo-relative paths that look like scratch or backup state."""
    root = Path(root)
    hits: list[str] = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if any(fnmatch.fnmatch(p.name, pat) for pat in SCRATCH_PATTERNS):
            hits.append(rel.as_posix())
    return sorted(set(hits))


def _iter_files(root: Path, pattern: str):
    for p in Path(root).rglob(pattern):
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield p, rel


def _magicmock_hits(root: Path) -> list[tuple[str, int]]:
    """MagicMock is banned in production code; tests may mock collaborators."""
    prod_skip = SKIP_DIRS | {"tests", "test", "testing"}
    hits: list[tuple[str, int]] = []
    for p, rel in _iter_files(root, "*.py"):
        if any(part in prod_skip for part in rel.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in re.finditer(
            r"^from unittest\.mock import MagicMock", text, re.MULTILINE
        ):
            hits.append((rel.as_posix(), text[: m.start()].count("\n") + 1))
    return hits


def _todo_hits(root: Path) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    for p, rel in _iter_files(root, "*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"#\s*TODO(?!\s*[\(\[])", text):
            hits.append((rel.as_posix(), text[: m.start()].count("\n") + 1))
    return hits


def _git_dirty(root: Path) -> tuple[list[str], str]:
    """Return (dirty entries, warning). A non-repo root warns instead of failing."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return [], "not a git repo (clean-tree check skipped)"
    if proc.returncode != 0:
        return [], "not a git repo (clean-tree check skipped)"
    return [line for line in proc.stdout.splitlines() if line.strip()], ""


def check(root: Path, *, require_clean: bool = False) -> tuple[bool, list[str]]:
    """Return (ok, messages) with ``fail:`` and ``warn:`` prefixes."""
    root = Path(root)
    messages: list[str] = []
    fails = 0

    for rel in scan_scratch_artifacts(root):
        messages.append(f"fail: scratch artifact present: {rel}")
        fails += 1

    for rel, line in _magicmock_hits(root):
        messages.append(f"fail: {rel}:{line} MagicMock import in non-test code")
        fails += 1

    if require_clean:
        dirty, warning = _git_dirty(root)
        if warning:
            messages.append(f"warn: {warning}")
        elif dirty:
            preview = ", ".join(dirty[:5])
            messages.append(
                f"fail: uncommitted changes present ({len(dirty)} path(s)): {preview}"
            )
            fails += 1

    for rel, line in _todo_hits(root):
        messages.append(f"warn: {rel}:{line} TODO without ticket ref")

    if fails:
        messages.append(f"{fails} hygiene failure(s)")
        return False, messages
    messages.append("repo hygiene ok")
    return True, messages


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument(
        "--require-clean",
        action="store_true",
        help="Fail when the git tree has uncommitted changes",
    )
    args = ap.parse_args(argv)

    ok, messages = check(args.root.resolve(), require_clean=args.require_clean)
    for message in messages:
        if message.startswith(("fail:", "warn:")):
            print(message)
        else:
            print("✅ " + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
