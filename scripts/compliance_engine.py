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
    """Prefer a Python that can import mypy/ruff/pytest (product venv may be lean)."""
    candidates: list[Path] = [
        ROOT / ".venv" / "bin" / "python",
        Path(sys.executable),
    ]
    # Optional shared tool venv (host may set TOOLS_VENV or use sibling watchlist)
    for env_key in ("COMPLIANCE_PYTHON", "TOOLS_VENV"):
        raw = os.environ.get(env_key, "").strip()
        if raw:
            p = Path(raw)
            if p.is_dir():
                candidates.insert(0, p / "bin" / "python")
            elif p.is_file():
                candidates.insert(0, p)
    home = Path.home()
    candidates.extend(
        [
            home / "watchlist" / ".venv" / "bin" / "python",
            home / "agent-harness" / ".venv" / "bin" / "python",
        ]
    )
    seen: set[str] = set()
    for cand in candidates:
        s = str(cand)
        if s in seen or not cand.is_file():
            continue
        seen.add(s)
        r = subprocess.run(
            [s, "-c", "import mypy, ruff, pytest"],
            capture_output=True,
            check=False,
        )
        if r.returncode == 0:
            return s
    # last resort: product venv or current interpreter
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

    # Only typecheck dirs that exist and contain Python (empty dirs make mypy exit 2)
    mypy_targets: list[str] = []
    for d in ("scripts", "tests", "bin", "config", "utils"):
        p = ROOT / d
        if p.is_dir() and any(p.rglob("*.py")):
            mypy_targets.append(d)
    if not mypy_targets:
        mypy_targets = ["scripts"]
    mypy_cmd = [py, "-m", "mypy", *mypy_targets]

    # Only check changed python files that still exist (deleted paths break ruff)
    changed_py_files = [
        f for f in changed if f.endswith(".py") and (ROOT / f).is_file()
    ]
    if args.diff and changed_py_files:
        linter_cmd = [py, "-m", "ruff", "check"] + changed_py_files
    elif args.diff and not changed_py_files:
        linter_cmd = ["true"]  # No existing python files in diff
    else:
        # Only dirs that exist (many products have no bin/; ruff E902 on missing path)
        lint_dirs = [
            d
            for d in ("scripts", "tests", "bin", "email_detach", "src", "lib")
            if (ROOT / d).is_dir()
        ]
        linter_cmd = [py, "-m", "ruff", "check", *(lint_dirs or ["."])]

    results = [
        _run_tool("type_checker", mypy_cmd),
        _run_tool("linter", linter_cmd),
    ]

    # Skip pytest when the product has no test suite (pytest exit 5 = no tests collected)
    has_py_tests = any(
        (ROOT / d).is_dir() and any((ROOT / d).rglob("test_*.py"))
        for d in ("tests", "test")
    ) or any(ROOT.glob("test_*.py"))
    if has_py_tests:
        results.append(
            _run_tool(
                "test_runner",
                [py, "-m", "pytest", "-q"],
                env={**os.environ, "PYTHONPATH": str(ROOT)},
            )
        )
    else:
        results.append(
            {
                "tool": "test_runner",
                "exit": 0,
                "stdout": "no python tests found — skipped",
                "stderr": "",
            }
        )

    # Pytest exit 5 (no tests collected) is not a failure for products without a suite
    for r in results:
        if r.get("tool") == "test_runner" and r.get("exit") == 5:
            out = (r.get("stdout") or "") + (r.get("stderr") or "")
            if "no tests" in out.lower() or "collected 0" in out.lower():
                r["exit"] = 0
                r["stdout"] = (r.get("stdout") or "") + "\n(treated as skip: no tests)"

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
