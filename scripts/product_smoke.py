#!/usr/bin/env python3
"""Run smoke commands from `.agents/product_plugin.yaml` (Phase 2)."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from product_plugin import load_plugin  # type: ignore


def run_smoke(
    product_root: Path,
    *,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Execute each smoke entry. Returns list of {name, cmd, cwd, exit, stdout, stderr}."""
    data = load_plugin(product_root)
    entries = data.get("smoke") or []
    if not isinstance(entries, list):
        return []

    results: list[dict[str, Any]] = []
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "unnamed")
        cmd = raw.get("cmd")
        if not isinstance(cmd, list) or not cmd:
            results.append(
                {
                    "name": name,
                    "cmd": cmd,
                    "cwd": ".",
                    "exit": 2,
                    "stdout": "",
                    "stderr": "invalid or empty cmd (need argv list)",
                }
            )
            continue
        cmd_s = [str(c) for c in cmd]
        cwd_rel = str(raw.get("cwd") or ".").strip() or "."
        cwd = (product_root / cwd_rel).resolve()
        if dry_run:
            results.append(
                {
                    "name": name,
                    "cmd": cmd_s,
                    "cwd": str(cwd),
                    "exit": 0,
                    "stdout": "dry-run",
                    "stderr": "",
                }
            )
            continue
        if not cwd.is_dir():
            results.append(
                {
                    "name": name,
                    "cmd": cmd_s,
                    "cwd": str(cwd),
                    "exit": 2,
                    "stdout": "",
                    "stderr": f"cwd does not exist: {cwd}",
                }
            )
            continue
        proc = subprocess.run(
            cmd_s,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            {
                "name": name,
                "cmd": cmd_s,
                "cwd": str(cwd),
                "exit": int(proc.returncode),
                "stdout": (proc.stdout or "")[-2000:],
                "stderr": (proc.stderr or "")[-2000:],
            }
        )
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run product_plugin smoke commands")
    ap.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Product repo root (default: cwd)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = args.root.expanduser().resolve()
    results = run_smoke(root, dry_run=args.dry_run)
    if not results:
        print("⚠️  no smoke entries in .agents/product_plugin.yaml")
        return 0
    failed = 0
    for r in results:
        tag = "✅" if r["exit"] == 0 else "❌"
        print(f"{tag} smoke:{r['name']} exit={r['exit']} cmd={r['cmd']} cwd={r['cwd']}")
        if r["exit"] != 0:
            failed += 1
            if r.get("stderr"):
                print(r["stderr"][-500:])
    if failed:
        print(f"❌ {failed}/{len(results)} smoke step(s) failed")
        return 1
    print(f"✅ {len(results)} smoke step(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
