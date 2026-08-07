#!/usr/bin/env python3
"""Bounded scan: ops/kanban scripts' hardcoded product paths must resolve.

Uses night_shift_products.yaml as the product map. Only scans known consumer
filenames (not full $HOME).

  python3 scripts/check_product_path_consumers.py
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parent.parent
CONSUMERS = (
    "scripts/ops_dashboard.py",
    "scripts/kanban_ensure_spec.py",
    "scripts/kanban_auto_execute.py",
)

# Path.home() / "foo"  or  ~/foo  or /home/user/foo
HOME_DIV = re.compile(
    r'Path\.home\(\)\s*/\s*["\']([A-Za-z0-9._-]+)["\']'
)
TILDE = re.compile(r'["\']~/([A-Za-z0-9._-]+)["\']')
ABS = re.compile(r'["\'](/home/[^"\']+)["\']')


def load_product_dirs(products_file: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    if not products_file.is_file():
        return out
    for line in products_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        line = line.lstrip("-").strip()
        pid, proot = line.split(":", 1)
        pid = pid.strip()
        p = Path(proot.strip().strip("\"'")).expanduser()
        out[pid] = p
    return out


def extract_home_basenames(text: str) -> set[str]:
    names: set[str] = set()
    for m in HOME_DIV.finditer(text):
        names.add(m.group(1))
    for m in TILDE.finditer(text):
        names.add(m.group(1))
    for m in ABS.finditer(text):
        names.add(Path(m.group(1)).name)
    return names


def check(products_file: Path, home: Path | None = None) -> list[str]:
    home = home or Path.home()
    products = load_product_dirs(products_file)
    # basenames that are registered products
    registered = {p.name for p in products.values()}
    registered |= set(products.keys())
    # also map basename -> path for existence
    by_base: dict[str, Path] = {}
    for pid, p in products.items():
        by_base[p.name] = p
        by_base[pid] = p

    errs: list[str] = []
    # Scan harness + each product root for consumer files
    roots = [HARNESS_ROOT, *[p for p in products.values() if p.is_dir()]]
    seen_files: set[Path] = set()
    for root in roots:
        for rel in CONSUMERS:
            fp = (root / rel).resolve()
            if fp in seen_files or not fp.is_file():
                continue
            seen_files.add(fp)
            text = fp.read_text(encoding="utf-8", errors="replace")
            for base in extract_home_basenames(text):
                # Only enforce basenames that look like known product dirs
                if base not in by_base and base not in registered:
                    continue
                target = by_base.get(base) or (home / base)
                if not target.expanduser().is_dir():
                    errs.append(
                        f"{fp}: references {base!r} but directory missing: {target}"
                    )
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--products-file",
        type=Path,
        default=None,
    )
    args = ap.parse_args(argv)
    pf = args.products_file
    if pf is None:
        env = os.environ.get("NIGHT_SHIFT_PRODUCTS_FILE")
        pf = Path(env) if env else HARNESS_ROOT / "config" / "night_shift_products.yaml"
    pf = pf.expanduser()
    errs = check(pf)
    if errs:
        print("check_product_path_consumers: FAIL", file=sys.stderr)
        for e in errs[:40]:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("check_product_path_consumers: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
