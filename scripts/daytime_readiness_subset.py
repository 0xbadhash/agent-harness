#!/usr/bin/env python3
"""Daytime subset of night_shift gates — catch red before 03:15 HKT.

Runs per product (from config/night_shift_products.yaml or --root):
  1. check_hardcodes
  2. validate full (when scripts/validate.py exists)
  3. product_smoke (when scripts/product_smoke.py exists)

Exit 0 only if all selected products pass. Does not write vault logs.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS = HARNESS / "config" / "night_shift_products.yaml"


def _load_products(path: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        pid, raw = line.split(":", 1)
        raw = raw.strip()
        root = Path(os.path.expanduser(raw)).resolve()
        out.append((pid.strip(), root))
    return out


def _run(cmd: list[str], cwd: Path) -> int:
    print(f"  $ {' '.join(cmd)}  (cwd={cwd})")
    r = subprocess.run(cmd, cwd=str(cwd), check=False)
    return int(r.returncode)


def gate_product(pid: str, root: Path) -> int:
    print(f"\n=== {pid} ({root}) ===")
    if not root.is_dir():
        print("❌ missing root")
        return 1
    rc = 0
    hc = root / "scripts" / "check_hardcodes.py"
    if hc.is_file():
        if _run([sys.executable, str(hc)], root) != 0:
            rc = 1
    else:
        print("  skip hardcodes (no script)")
    val = root / "scripts" / "validate.py"
    if val.is_file():
        env = os.environ.copy()
        # Prefer product venv / shared tools for ruff/pytest
        for cand in (
            root / ".venv" / "bin" / "python",
            Path.home() / "watchlist" / ".venv" / "bin" / "python",
        ):
            if cand.is_file():
                env["COMPLIANCE_PYTHON"] = str(cand)
                break
        r = subprocess.run(
            [sys.executable, str(val), "full"],
            cwd=str(root),
            env=env,
            check=False,
        )
        if r.returncode != 0:
            rc = 1
    else:
        print("  skip validate (no script)")
    smoke = root / "scripts" / "product_smoke.py"
    if smoke.is_file():
        if _run([sys.executable, str(smoke), "--root", str(root)], root) != 0:
            rc = 1
    else:
        print("  skip product_smoke (no script)")
    print(f"{'✅' if rc == 0 else '❌'} {pid}")
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--products-file", type=Path, default=DEFAULT_PRODUCTS)
    ap.add_argument(
        "--root",
        action="append",
        default=[],
        help="Product root (repeatable). If set, ignores products file.",
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="Product id filter when using products file",
    )
    args = ap.parse_args(argv)
    if args.root:
        products = [(Path(r).name, Path(r).resolve()) for r in args.root]
    else:
        products = _load_products(args.products_file)
        if args.only:
            want = set(args.only)
            products = [(i, p) for i, p in products if i in want]
    if not products:
        print("No products", file=sys.stderr)
        return 2
    failed = 0
    for pid, root in products:
        failed += gate_product(pid, root)
    print(f"\n{'✅ daytime subset PASS' if failed == 0 else f'❌ daytime subset FAIL ({failed} product(s))'}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
