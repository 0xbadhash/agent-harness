#!/usr/bin/env python3
"""Tier A-3: merge critical SoT scripts into products (optional --apply).

Default: report-only. With --apply: copy SoT over product (backup .bak-sot-merge).
Does not remove protect-list entries (product may still protect other forks).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
DEFAULT_LIST = HARNESS / "config" / "critical_sot_scripts.txt"
PRODUCTS = HARNESS / "config" / "night_shift_products.yaml"


def _sha(p: Path) -> str | None:
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load_list(path: Path) -> list[str]:
    out: list[str] = []
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def _products() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    if not PRODUCTS.is_file():
        return out
    for line in PRODUCTS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        pid, raw = line.split(":", 1)
        if pid.strip() == "agent-harness":
            continue
        out.append((pid.strip(), Path(os.path.expanduser(raw.strip())).resolve()))
    return out


def merge_one(
    sot: Path, product: Path, rels: list[str], *, apply: bool
) -> list[str]:
    notes: list[str] = []
    for rel in rels:
        src, dst = sot / rel, product / rel
        if not src.is_file():
            continue
        ss, ds = _sha(src), _sha(dst)
        if ds is None:
            notes.append(f"{rel}:missing")
            if apply:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                notes[-1] += "→copied"
            continue
        if ss == ds:
            continue
        notes.append(f"{rel}:diverged")
        if apply:
            bak = dst.with_suffix(dst.suffix + ".bak-sot-merge")
            shutil.copy2(dst, bak)
            shutil.copy2(src, dst)
            notes[-1] += f"→merged (bak {bak.name})"
    return notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="Copy SoT over product forks")
    ap.add_argument("--list", type=Path, default=DEFAULT_LIST)
    args = ap.parse_args(argv)
    rels = _load_list(args.list)
    any_div = False
    for pid, root in _products():
        if not root.is_dir():
            print(f"⚠️  {pid}: missing {root}")
            continue
        notes = merge_one(HARNESS, root, rels, apply=bool(args.apply))
        if notes:
            any_div = True
            print(f"{pid}: {', '.join(notes)}")
        else:
            print(f"{pid}: ok (critical SoT match)")
    if args.apply:
        print("✅ protect_sot_merge --apply done")
    else:
        print("report-only (pass --apply to merge)")
    return 0 if not any_div or args.apply else 0  # report always 0


if __name__ == "__main__":
    sys.exit(main())
