#!/usr/bin/env python3
"""Ratcheting lint gate: a rule may fall, never rise above its baseline.

Baseline data (per-rule violation counts) lives in
``config/lint_ratchet_baseline.json``. The gate runs ruff (or reads a saved
ruff JSON report), compares counts per rule code, and:

- fails when a rule's count is **above** its baseline;
- passes when counts are equal or lower (the ratchet only tightens);
- treats a rule absent from the baseline as 0, so new rule codes are gated.

Lowering a count does not rewrite the baseline automatically; pass ``--update``
after a clean run to record the new (lower) floor.

Usage::

  python3 scripts/check_lint_ratchet.py
  python3 scripts/check_lint_ratchet.py --report /tmp/ruff.json
  python3 scripts/check_lint_ratchet.py --update
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
BASELINE_NAME = "lint_ratchet_baseline.json"
DEFAULT_BASELINE = ROOT / "config" / BASELINE_NAME


def load_baseline(path: Path = DEFAULT_BASELINE) -> dict[str, int]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: baseline must be a JSON object")
    return {str(k): int(v) for k, v in data.items()}


def count_by_rule(report: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(item.get("code")) for item in report if item.get("code"))
    return dict(sorted(counts.items()))


def compare(
    counts: dict[str, int], baseline: dict[str, int]
) -> tuple[bool, list[str]]:
    """Return (ok, messages). Only increases fail; drops are reported."""
    failures: list[str] = []
    messages: list[str] = []
    for rule in sorted(set(counts) | set(baseline)):
        now = int(counts.get(rule, 0))
        floor = int(baseline.get(rule, 0))
        if now > floor:
            failures.append(f"{rule}: {now} > baseline {floor}")
        elif now < floor:
            messages.append(f"ratchet: {rule} improved {floor} → {now}")
        else:
            messages.append(f"ratchet: {rule} held at {now}")
    if failures:
        return False, ["lint ratchet regression: " + "; ".join(failures)]
    return True, messages or ["ok: no lint violations recorded"]


def _ruff_command(root: Path) -> list[str] | None:
    found = shutil.which("ruff")
    if found:
        return [found, "check", "--output-format=json", "--no-fix", "."]
    candidate = root / ".venv" / "bin" / "ruff"
    if candidate.is_file():
        return [str(candidate), "check", "--output-format=json", "--no-fix", "."]
    try:
        import ruff  # noqa: F401

        return [sys.executable, "-m", "ruff", "check", "--output-format=json", "--no-fix", "."]
    except ImportError:
        return None


def run_ruff(root: Path) -> list[dict[str, Any]]:
    cmd = _ruff_command(root)
    if cmd is None:
        raise RuntimeError("ruff not found — install ruff or pass --report")
    proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, check=False)
    if not proc.stdout.strip():
        if proc.returncode == 0:
            return []
        raise RuntimeError((proc.stderr or "ruff produced no JSON").strip()[:400])
    return json.loads(proc.stdout)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    ap.add_argument("--report", type=Path, default=None, help="Saved ruff JSON")
    ap.add_argument("--update", action="store_true", help="Write current counts as the floor")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    baseline_path = args.baseline
    if not baseline_path.is_absolute():
        baseline_path = root / baseline_path
    try:
        baseline = load_baseline(baseline_path)
        report = (
            json.loads(args.report.read_text(encoding="utf-8"))
            if args.report is not None
            else run_ruff(root)
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"❌ lint ratchet unavailable: {exc}")
        return 1

    counts = count_by_rule(report)
    if args.update:
        baseline_path.write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")
        print(f"✅ ratchet baseline updated: {baseline_path} {counts}")
        return 0

    ok, messages = compare(counts, baseline)
    for message in messages:
        print(("✅ " if ok else "❌ ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
