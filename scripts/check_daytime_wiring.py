#!/usr/bin/env python3
"""A3 — verify daytime readiness wiring artifacts exist (no host enable).

Checks (harness root):
  - .github/workflows/daytime-gates.yml
  - deploy/daytime-gates.service + .timer
  - scripts/daytime_readiness_subset.py
  - templates/daytime-gates.yml (product-copy template)
  - scripts/install_daytime_timer.sh

Optional: --product PATH (repeatable) with --require-product-workflow
to assert each product has .github/workflows/daytime-gates.yml.
Exit 0 if all required pieces present.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

HARNESS_REQUIRED = (
    ".github/workflows/daytime-gates.yml",
    "deploy/daytime-gates.service",
    "deploy/daytime-gates.timer",
    "scripts/daytime_readiness_subset.py",
    "scripts/install_daytime_timer.sh",
    "templates/daytime-gates.yml",
)


@dataclass
class WiringResult:
    ok: bool
    present: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


def evaluate(
    root: Path,
    products: list[Path] | None = None,
    require_product_workflow: bool = False,
) -> WiringResult:
    present: list[str] = []
    missing: list[str] = []
    root = root.resolve()
    for rel in HARNESS_REQUIRED:
        p = root / rel
        if p.is_file():
            present.append(rel)
        else:
            missing.append(rel)

    if products and require_product_workflow:
        for prod in products:
            prod = prod.resolve()
            wf = prod / ".github" / "workflows" / "daytime-gates.yml"
            label = f"product:{prod.name}:.github/workflows/daytime-gates.yml"
            if wf.is_file():
                present.append(label)
            else:
                missing.append(label)

    return WiringResult(ok=len(missing) == 0, present=present, missing=missing)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--product",
        type=Path,
        action="append",
        default=[],
        help="Product root to check (repeatable)",
    )
    ap.add_argument(
        "--require-product-workflow",
        action="store_true",
        help="Fail if --product roots lack daytime-gates.yml",
    )
    args = ap.parse_args(argv)
    r = evaluate(
        args.root,
        products=list(args.product) or None,
        require_product_workflow=args.require_product_workflow,
    )
    print(f"daytime_wiring ok={r.ok}")
    for p in r.present:
        print(f"  ✅ {p}")
    for m in r.missing:
        print(f"  ❌ missing {m}")
    return 0 if r.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
