#!/usr/bin/env python3
"""G6 — when lockfiles change, run available audit tools (fail closed if findings).

If no audit tool is installed, warn and exit 0 (do not block offline sandboxes).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

LOCK_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "requirements-lock.txt",
    "Pipfile.lock",
    "poetry.lock",
    "uv.lock",
    "Cargo.lock",
}


def _changed(repo: Path, base: str, head: str) -> list[str]:
    for sep in ("...", ".."):
        r = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}{sep}{head}"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0:
            return [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    return []


def check(repo: Path, base: str, head: str) -> tuple[bool, list[str]]:
    repo = repo.resolve()
    locks = [c for c in _changed(repo, base, head) if Path(c).name in LOCK_NAMES]
    if not locks:
        return True, ["ok: no lockfile changes"]

    msgs: list[str] = [f"lockfiles: {', '.join(locks)}"]
    ran = False
    failed = False

    if any(Path(c).name in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock"} for c in locks):
        if shutil.which("npm") and (repo / "package.json").is_file():
            ran = True
            r = subprocess.run(
                ["npm", "audit", "--audit-level=high"],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=False,
            )
            if r.returncode != 0:
                failed = True
                msgs.append("npm audit reported high+ issues")
            else:
                msgs.append("npm audit clean (high+)")

    py_locks = any(
        Path(c).name in {"requirements.txt", "requirements-lock.txt", "Pipfile.lock", "poetry.lock", "uv.lock"}
        for c in locks
    )
    if py_locks:
        pip_audit = shutil.which("pip-audit")
        if pip_audit:
            ran = True
            r = subprocess.run(
                [pip_audit],
                cwd=str(repo),
                capture_output=True,
                text=True,
                check=False,
            )
            if r.returncode != 0:
                failed = True
                msgs.append("pip-audit reported issues")
            else:
                msgs.append("pip-audit clean")

    if not ran:
        msgs.append("warn: no audit tool available — skipped (install npm or pip-audit for fail-closed)")
        return True, msgs
    if failed:
        return False, msgs
    return True, msgs


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
