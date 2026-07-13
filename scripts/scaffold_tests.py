#!/usr/bin/env python3
"""TDD Red-phase generator. Creates failing test stubs for a roadmap task."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEMPLATE = '''"""Auto-generated Red-phase test for task: {task}."""
import pytest


def test_{safe_name}_behavior():
    """Public contract assertion — entry → validated output."""
    # TODO(TICKET-101): replace with real assertion after implementation
    raise NotImplementedError("Red phase: implement to make this pass")


def test_{safe_name}_edge_case():
    """Boundary / invariant check."""
    raise NotImplementedError("Red phase: implement to make this pass")
'''

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="Roadmap task name")
    ap.add_argument("--module", required=True, help="Target module path (e.g. api.processing)")
    ap.add_argument("--out", help="Optional explicit output path")
    args = ap.parse_args()

    safe = args.task.lower().replace(" ", "_").replace("-", "_")[:60]
    root = Path(__file__).resolve().parent.parent
    out = Path(args.out) if args.out else root / "tests" / f"test_{safe}.py"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists():
        print(f"⚠️  {out} already exists — not overwriting")
        return 0

    out.write_text(TEMPLATE.format(task=args.task, safe_name=safe), encoding="utf-8")
    print(f"✅ scaffolded {out}")
    print(f"🔴 Red phase: run your test runner on {out} — it MUST fail")
    return 0

if __name__ == "__main__":
    sys.exit(main())
