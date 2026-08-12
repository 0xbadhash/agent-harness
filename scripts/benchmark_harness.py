#!/usr/bin/env python3
"""Tier C-1: micro-benchmark of harness gate scripts (scaffold).

  python3 scripts/benchmark_harness.py --root .
"""
from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
DEFAULT_CMDS = (
    [sys.executable, str(SCRIPTS / "check_harness_manifest.py"), "--root", "{root}"],
    [sys.executable, str(SCRIPTS / "check_compatibility.py"), "--root", "{root}"],
    [sys.executable, str(SCRIPTS / "check_pi_fixtures.py"), "--root", "{root}"],
    [sys.executable, str(SCRIPTS / "pipeline_state.py"), "get"],
)


def _run_once(cmd: list[str], cwd: Path) -> float:
    t0 = time.perf_counter()
    subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return time.perf_counter() - t0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--rounds", type=int, default=3)
    args = ap.parse_args(argv)
    root = args.root.resolve()
    print(f"# harness micro-benchmark root={root} rounds={args.rounds}")
    for tmpl in DEFAULT_CMDS:
        cmd = [c.format(root=str(root)) for c in tmpl]
        name = Path(cmd[1]).name if len(cmd) > 1 else cmd[0]
        times = [_run_once(cmd, root) for _ in range(max(1, args.rounds))]
        med = statistics.median(times)
        print(f"{name}: median={med*1000:.1f}ms n={len(times)}")
    print("✅ benchmark_harness scaffold complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
