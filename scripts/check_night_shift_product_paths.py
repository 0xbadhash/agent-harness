#!/usr/bin/env python3
"""Fail closed if night_shift product paths are missing or non-portable.

Portable policy: committed yaml must use ~/... or $HOME-relative paths,
not absolute /home/<user>/... (see config/night_shift_products.yaml header).

  python3 scripts/check_night_shift_product_paths.py
  python3 scripts/check_night_shift_product_paths.py --products-file PATH
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parent.parent
ABS_HOME = re.compile(r"^/home/[^/\s]+/")


def parse_products_yaml(text: str) -> list[tuple[str, str]]:
    """Return (product_id, raw_path_string) for each configured row."""
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        raw = raw.lstrip("-").strip()
        if ":" not in raw:
            continue
        pid, proot = raw.split(":", 1)
        pid = pid.strip()
        path_s = proot.strip().strip("\"'")
        if not pid or not path_s:
            continue
        rows.append((pid, path_s))
    return rows


def is_non_portable_abs_home(path_s: str) -> bool:
    s = path_s.strip()
    if s.startswith("~/") or s.startswith("$HOME/") or s.startswith("${HOME}/"):
        return False
    return bool(ABS_HOME.match(s)) or s.startswith("/home/")


def check_products(
    rows: list[tuple[str, str]],
    *,
    require_exists: bool = True,
) -> list[str]:
    """Return list of error messages (empty = OK)."""
    errs: list[str] = []
    seen: set[str] = set()
    for pid, path_s in rows:
        if pid in seen:
            errs.append(f"duplicate product id: {pid}")
        seen.add(pid)
        if is_non_portable_abs_home(path_s):
            errs.append(
                f"{pid}: non-portable absolute home path {path_s!r} "
                f"(use ~/... or $HOME/...)"
            )
        expanded = Path(path_s).expanduser()
        if require_exists and not expanded.is_dir():
            errs.append(f"{pid}: path missing or not a directory: {expanded}")
    return errs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--products-file",
        type=Path,
        default=None,
        help="Override products yaml (default: harness config or env)",
    )
    ap.add_argument(
        "--allow-missing",
        action="store_true",
        help="Only check portability, not directory existence",
    )
    args = ap.parse_args(argv)

    path = args.products_file
    if path is None:
        env = os.environ.get("NIGHT_SHIFT_PRODUCTS_FILE")
        path = Path(env) if env else HARNESS_ROOT / "config" / "night_shift_products.yaml"
    path = path.expanduser()
    if not path.is_file():
        print(f"❌ products file missing: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    rows = parse_products_yaml(text)
    if not rows:
        print(f"❌ no products parsed from {path}", file=sys.stderr)
        return 2

    errs = check_products(rows, require_exists=not args.allow_missing)
    for pid, path_s in rows:
        exp = Path(path_s).expanduser()
        status = "OK" if exp.is_dir() else "MISSING"
        if is_non_portable_abs_home(path_s):
            status = "NONPORTABLE"
        print(f"  {status:12} {pid:20} {path_s} -> {exp}")

    if errs:
        print("check_night_shift_product_paths: FAIL", file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        return 1
    print(f"check_night_shift_product_paths: OK ({len(rows)} product(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
