#!/usr/bin/env python3
"""Fail-closed product-trait category gate (web / web3 / client_secrets).

Wired into hard_gates. Scaffold named stubs via scaffold_web_e2e.py.

  python3 scripts/check_product_traits.py --root .
  python3 scripts/check_product_traits.py --root /tmp/fixture --json

Dry miss: fixture with traits.web3=true and no isolation S-id → EXIT 1.
Web-only products without web3 signals are not forced to grow isolation stubs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from product_trait_contract import evaluate_categories, infer_traits  # noqa: E402


def check(root: Path) -> tuple[bool, list[str]]:
    ok, msgs, _detail = evaluate_categories(root.resolve())
    return ok, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--infer-only",
        action="store_true",
        help="Print inferred traits and exit 0 (no category fail-closed)",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()

    if args.infer_only:
        traits = infer_traits(root)
        if args.json:
            print(json.dumps(traits, indent=2))
        else:
            for name, info in traits.items():
                state = "ON" if info.get("active") else "off"
                print(f"trait:{name} {state} mode={info.get('mode')} reasons={info.get('reasons')}")
        return 0

    ok, msgs, detail = evaluate_categories(root)
    if args.json:
        print(json.dumps({"pass": ok, "messages": msgs, "detail": detail}, indent=2))
    else:
        for m in msgs:
            prefix = "✅ " if m.startswith("ok:") else ("❌ " if m.startswith("fail:") else "· ")
            print(prefix + m)
        print(
            "✅ check_product_traits ok"
            if ok
            else "❌ check_product_traits FAIL (missing required test categories)"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
