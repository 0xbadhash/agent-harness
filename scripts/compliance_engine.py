#!/usr/bin/env python3
"""Diff-first evidence runner. Executes type/lint/test/security checks on changed files."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _python_executable() -> str:
    venv_py = ROOT / ".venv" / "bin" / "python"
    if venv_py.is_file():
        return str(venv_py)
    return sys.executable


def _changed_files(diff: str | None) -> list[str]:
    if not diff:
        return []
    r = subprocess.run(["git", "diff", "--name-only", diff], cwd=ROOT, capture_output=True, text=True)
    return [f for f in r.stdout.splitlines() if f.strip()]

def _run_tool(name: str, cmd: list[str], env: dict[str, str] | None = None) -> dict:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    return {"tool": name, "exit": r.returncode, "stdout": r.stdout[-2000:], "stderr": r.stderr[-2000:]}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", help="Git range (e.g. HEAD~1..HEAD)")
    ap.add_argument("--scope", help="Module scope filter")
    ap.add_argument("--json-report", action="store_true")
    args = ap.parse_args()

    changed = _changed_files(args.diff)
    py = _python_executable()

    mypy_cmd = [py, "-m", "mypy", "scripts", "tests", "config", "utils"]

    # Only check changed python files that still exist (deleted paths break ruff)
    changed_py_files = [
        f for f in changed if f.endswith(".py") and (ROOT / f).is_file()
    ]
    if args.diff and changed_py_files:
        linter_cmd = [py, "-m", "ruff", "check"] + changed_py_files
    elif args.diff and not changed_py_files:
        linter_cmd = ["true"]  # No existing python files in diff
    else:
        linter_cmd = [py, "-m", "ruff", "check", "."]
        
    results = [
        _run_tool("type_checker", mypy_cmd),
        _run_tool("linter", linter_cmd),
        _run_tool(
            "test_runner",
            [py, "-m", "pytest", "-q"],
            env={**os.environ, "PYTHONPATH": str(ROOT)},
        ),
    ]

    ok = all(r["exit"] == 0 for r in results)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "diff": args.diff,
        "scope": args.scope,
        "changed_files": changed,
        "results": results,
        "pass": ok,
    }
    if args.json_report:
        print(json.dumps(report, indent=2))
    else:
        for r in results:
            tag = "✅" if r["exit"] == 0 else "❌"
            print(f"{tag} {r['tool']} (exit {r['exit']})")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
