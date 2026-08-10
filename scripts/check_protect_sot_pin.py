#!/usr/bin/env python3
"""G15 — warn (exit 0) or --strict fail when protect-list FSM scripts diverge from SoT.

Default: warn only. Used by portfolio_install_report and optional hard_gates warn path.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# Critical scripts that should rarely fork after HSQ-2
PIN_SCRIPTS = (
    "scripts/pipeline_state.py",
    "scripts/hard_gates.py",
)


def _sha(p: Path) -> str | None:
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_product(sot: Path, product: Path) -> list[str]:
    drift: list[str] = []
    for rel in PIN_SCRIPTS:
        ss, ps = _sha(sot / rel), _sha(product / rel)
        if ss is None or ps is None:
            continue
        if ss != ps:
            drift.append(rel)
    return drift


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sot", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--product", type=Path, required=True)
    ap.add_argument("--strict", action="store_true", help="exit 1 on drift")
    args = ap.parse_args(argv)
    drift = check_product(args.sot.resolve(), args.product.resolve())
    if not drift:
        print(f"✅ protect SoT pin ok ({args.product})")
        return 0
    msg = f"protect SoT drift: {', '.join(drift)} (see docs/protect-list-merge.md)"
    if args.strict:
        print(f"❌ {msg}", file=sys.stderr)
        return 1
    print(f"⚠️  {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
