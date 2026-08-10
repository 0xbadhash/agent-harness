#!/usr/bin/env python3
"""G14 — py_compile every changed .py file on the ship diff (disk is truth).

Usage::

  python3 scripts/check_diff_compile.py --base HEAD~1 --head HEAD
"""
from __future__ import annotations

import argparse
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path


def _changed_py(repo: Path, base: str, head: str) -> list[Path]:
    r = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...{head}"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        # fallback two-dot
        r = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}..{head}"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
    out: list[Path] = []
    for line in (r.stdout or "").splitlines():
        rel = line.strip()
        if not rel.endswith(".py"):
            continue
        p = repo / rel
        if p.is_file():
            out.append(p)
    return out


def check(repo: Path, base: str, head: str) -> tuple[bool, list[str]]:
    repo = repo.resolve()
    files = _changed_py(repo, base, head)
    if not files:
        return True, ["ok: no changed .py files"]
    bad: list[str] = []
    for p in files:
        try:
            # compile to temp to avoid writing .pyc into tree
            with tempfile.NamedTemporaryFile(suffix=".pyc", delete=True) as tmp:
                py_compile.compile(str(p), cfile=tmp.name, doraise=True)
        except py_compile.PyCompileError as e:
            bad.append(f"{p.relative_to(repo)}: {e.msg}")
        except OSError as e:
            bad.append(f"{p.relative_to(repo)}: {e}")
    if bad:
        return False, bad
    return True, [f"ok: py_compile {len(files)} file(s)"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args(argv)
    ok, msgs = check(args.repo.resolve(), args.base, args.head)
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
