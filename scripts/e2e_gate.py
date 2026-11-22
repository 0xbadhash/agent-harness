#!/usr/bin/env python3
"""Run one product's Playwright scenarios and write an E2E gate.

Exit 0 pass, 1 fail, 2 refused Chromium build. Does not edit the product.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playwright_chromium_guard import main as guard_main  # noqa: E402

MARKER = "E2E-GATE"
GLOBS = (
    "tests/e2e/**/*.spec.ts",
    "tests/e2e/**/*.spec.js",
    "e2e/**/*.spec.ts",
    "e2e/**/*.spec.js",
    "tests/e2e/**/*_test.py",
)


def discover(root: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in GLOBS:
        found.extend(p for p in root.glob(pattern) if p.is_file())
    return sorted(set(found))


def chromium_version(explicit: str | None) -> str:
    if explicit is not None:
        return explicit.strip()
    try:
        proc = subprocess.run(
            ["chromium", "--version"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    parts = (proc.stdout or proc.stderr or "").split()
    return parts[-1] if parts else ""


def write_report(path: Path, status: str, root: Path, scenarios: list[Path], detail: str) -> None:
    names = "\n".join(f"- {p.relative_to(root)}" for p in scenarios) or "- (none)"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {MARKER}\n\nstatus: {status}\nproduct: {root}\n\n## Scenarios\n\n{names}\n\n## Detail\n\n{detail}\n",
        encoding="utf-8",
    )


def run_gate(
    root: Path,
    report: Path,
    version: str | None = None,
    runner: list[str] | None = None,
) -> int:
    root = root.resolve()
    ver = chromium_version(version)
    if guard_main(["playwright_chromium_guard.py", ver]) != 0:
        write_report(report, "FAIL", root, [], f"refused chromium {ver}")
        return 2
    scenarios = discover(root)
    if not scenarios:
        write_report(report, "FAIL", root, [], "no Playwright scenarios found")
        return 1
    cmd = runner if runner is not None else ["npx", "playwright", "test"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=int(os.environ.get("E2E_GATE_TIMEOUT", "900")),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        write_report(report, "FAIL", root, scenarios, str(exc))
        return 1
    tail = ((proc.stdout or "") + (proc.stderr or ""))[-2000:]
    if proc.returncode != 0:
        write_report(report, "FAIL", root, scenarios, tail or f"exit {proc.returncode}")
        return 1
    write_report(report, "PASS", root, scenarios, tail or "exit 0")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--chromium-version", default=None)
    ap.add_argument("--runner", default="", help="Override the Playwright command, as one shell string")
    args = ap.parse_args(argv)
    report = args.report or (args.root / ".agents" / "artifacts" / "E2E_GATE.md")
    runner = shlex.split(args.runner) if args.runner.strip() else None
    return run_gate(args.root, report, version=args.chromium_version, runner=runner)


if __name__ == "__main__":
    raise SystemExit(main())
