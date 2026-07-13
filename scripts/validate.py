#!/usr/bin/env python3
"""Unified validation entry point. Wraps compliance_engine + hygiene + hardcodes."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent

def _run(cmd: list[str], label: str) -> int:
    print(f"\n── {label} ──")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"❌ {label} failed (exit {r.returncode})")
    else:
        print(f"✅ {label} passed")
    return r.returncode

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["full", "hygiene", "compliance"])
    ap.add_argument("--diff", help="Git diff range, e.g. HEAD~1..HEAD")
    ap.add_argument("--scope", help="Module scope for compliance")
    args = ap.parse_args()
    py = sys.executable
    exits: list[int] = []

    if args.mode in ("full", "compliance"):
        cmd = [py, str(SCRIPTS / "compliance_engine.py")]
        if args.diff:
            cmd += ["--diff", args.diff]
        if args.scope:
            cmd += ["--scope", args.scope]
        exits.append(_run(cmd, "compliance_engine"))

    if args.mode in ("full", "hygiene"):
        exits.append(_run([py, str(SCRIPTS / "check_hardcodes.py")], "check_hardcodes"))
        exits.append(_run([py, str(SCRIPTS / "check_repo_hygiene.py")], "check_repo_hygiene"))
        exits.append(_run([py, str(SCRIPTS / "check_module_coverage.py")], "check_module_coverage"))

    failed = sum(1 for e in exits if e != 0)
    print(f"\n{'='*40}\n{len(exits)-failed}/{len(exits)} gates passed")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
