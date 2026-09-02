#!/usr/bin/env python3
"""Session/edit guard: protected paths + optional no-test-rewrite on fix diffs.

Portable stand-in for host PreToolUse hooks. Run on a git diff (hard_gates)
or as a pre-commit hook.

  python3 scripts/check_edit_guard.py --root .
  python3 scripts/check_edit_guard.py --root . --fix-task   # block test file edits
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

DEFAULT_PROTECTED = (
    ".env",
    ".env.local",
    "secrets/",
    "credentials.json",
    "client_secret.json",
    ".ssh/",
)

TEST_PREFIXES = ("tests/", "test_", "e2e/")


def _diff_names(root: Path, base: str | None, head: str | None) -> list[str]:
    cmd = ["git", "diff", "--name-only"]
    if base and head:
        cmd.append(f"{base}...{head}")
    elif base:
        cmd.append(base)
    r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, check=False)
    if r.returncode != 0:
        r = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
    names = [ln.strip().replace("\\", "/") for ln in (r.stdout or "").splitlines() if ln.strip()]
    return names


def _is_protected(rel: str) -> bool:
    low = rel.lower()
    if Path(rel).name in {".env", ".env.local", "credentials.json", "client_secret.json"}:
        return True
    if low.endswith(".env") or "/.env." in low:
        return True
    for p in DEFAULT_PROTECTED:
        if rel == p or rel.startswith(p) or f"/{p.rstrip('/')}/" in f"/{rel}":
            return True
    return False


def _is_test(rel: str) -> bool:
    name = Path(rel).name
    if name.startswith("test_") and name.endswith(".py"):
        return True
    return any(rel.startswith(p) or f"/{p}" in rel for p in ("tests/", "e2e/"))


def _fix_task_from_draft(root: Path) -> bool:
    draft = root / "PR_DRAFT.md"
    if not draft.is_file():
        return False
    t = draft.read_text(encoding="utf-8", errors="replace").lower()
    if "edit_guard: allow_test_edits" in t:
        return False
    return bool(
        "hotfix" in t
        or "**spec waiver:** hotfix" in t
        or "bugfix" in t
        or "fix-task" in t
    )


def check(
    root: Path,
    *,
    base: str | None = None,
    head: str | None = None,
    fix_task: bool | None = None,
) -> tuple[bool, list[str]]:
    root = root.resolve()
    names = _diff_names(root, base, head)
    msgs: list[str] = []
    if not names:
        return True, ["ok: edit_guard (no diff names)"]

    for rel in names:
        if _is_protected(rel):
            msgs.append(f"fail: protected path in diff: `{rel}`")

    if fix_task is None:
        fix_task = _fix_task_from_draft(root)
    if fix_task:
        test_hits = [n for n in names if _is_test(n)]
        if test_hits:
            msgs.append(
                "fail: fix-task must not rewrite tests "
                f"({', '.join(test_hits[:8])}) — write the failing test first, "
                "or set `edit_guard: allow_test_edits` in PR_DRAFT"
            )

    if msgs:
        return False, msgs
    return True, [f"ok: edit_guard ({len(names)} path(s))"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--base", default=None)
    ap.add_argument("--head", default=None)
    ap.add_argument("--fix-task", action="store_true")
    args = ap.parse_args(argv)
    ok, msgs = check(
        args.root.resolve(),
        base=args.base,
        head=args.head,
        fix_task=True if args.fix_task else None,
    )
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
