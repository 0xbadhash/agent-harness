#!/usr/bin/env python3
"""G4 — execute red_cmd / green_cmd from PR_DRAFT when present (TDD proof).

- If TDD N/A / docs-only wording → skip ok
- If red_cmd present: must exit non-zero
- If green_cmd present: must exit zero
- Commands run with shell=False via shlex; timeout 60s; cwd=repo
"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from pathlib import Path

NA_RE = re.compile(
    r"TDD\s*N/?A|docs-only.*TDD|TDD.*docs-only|prose-only",
    re.I,
)
RED_RE = re.compile(
    r"red_cmd\s*[:=]\s*`([^`]+)`|red_cmd\s*[:=]\s*([^\n]+)",
    re.I,
)
GREEN_RE = re.compile(
    r"green_cmd\s*[:=]\s*`([^`]+)`|green_cmd\s*[:=]\s*([^\n]+)",
    re.I,
)


def _extract(pat: re.Pattern[str], text: str) -> str | None:
    m = pat.search(text)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").strip().strip("`").strip()


def _run(cmd: str, cwd: Path) -> int:
    # Prefer list form; allow simple shell-less commands
    try:
        argv = shlex.split(cmd)
    except ValueError:
        return 2
    if not argv:
        return 2
    try:
        r = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return int(r.returncode)
    except (OSError, subprocess.TimeoutExpired):
        return 124


def check(repo: Path, pr_draft: Path) -> tuple[bool, list[str]]:
    repo = repo.resolve()
    if not pr_draft.is_file():
        return False, ["PR_DRAFT.md missing"]
    text = pr_draft.read_text(encoding="utf-8", errors="replace")
    if NA_RE.search(text) and not RED_RE.search(text) and not GREEN_RE.search(text):
        return True, ["ok: TDD N/A / docs-only"]

    red = _extract(RED_RE, text)
    green = _extract(GREEN_RE, text)
    if not red and not green:
        # hard_gates still requires red-proof wording; we only execute when cmds present
        if re.search(r"red.?proof|TDD", text, re.I):
            return True, ["ok: red-proof narrative without executable cmds"]
        return False, ["need red_cmd/green_cmd or TDD N/A"]

    msgs: list[str] = []
    if red:
        # allow true/false builtins
        if red in {"false", "/bin/false"}:
            code = 1
        elif red in {"true", "/bin/true"}:
            code = 0
        else:
            code = _run(red, repo)
        if code == 0:
            return False, [f"red_cmd must fail (exit non-zero); got 0 for: {red}"]
        msgs.append(f"ok: red_cmd failed as expected (exit {code})")
    if green:
        if green in {"true", "/bin/true"}:
            code = 0
        elif green in {"false", "/bin/false"}:
            code = 1
        else:
            code = _run(green, repo)
        if code != 0:
            return False, [f"green_cmd must pass (exit 0); got {code} for: {green}"]
        msgs.append("ok: green_cmd passed")
    return True, msgs or ["ok"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    args = ap.parse_args(argv)
    root = args.repo.resolve()
    draft = args.pr_draft or (root / "PR_DRAFT.md")
    ok, msgs = check(root, draft)
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
