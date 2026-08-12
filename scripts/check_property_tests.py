#!/usr/bin/env python3
"""J14 — modules listed under product_plugin property_tests must have tests.

plugin example::

  property_tests:
    enabled: true
    modules:
      - email_detach/parser
      - scripts/web_e2e_contract

Fail if enabled and a module has no matching test file/content reference.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def _load_modules(root: Path) -> tuple[bool, list[str]]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from product_plugin import load_plugin  # type: ignore

        data = load_plugin(root)
    except Exception:
        return False, []
    block = data.get("property_tests") or {}
    if not isinstance(block, dict):
        return False, []
    enabled = bool(block.get("enabled", False))
    mods = block.get("modules") or []
    if not isinstance(mods, list):
        return enabled, []
    return enabled, [str(m).strip() for m in mods if str(m).strip()]


def _tests_blob(root: Path) -> str:
    chunks: list[str] = []
    for base in (root / "tests",):
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            try:
                chunks.append(p.read_text(encoding="utf-8", errors="replace"))
                chunks.append(str(p))
            except OSError:
                continue
    return "\n".join(chunks)


def check(root: Path) -> tuple[bool, list[str]]:
    root = root.resolve()
    enabled, modules = _load_modules(root)
    if not enabled or not modules:
        return True, ["ok: property_tests disabled or empty"]
    blob = _tests_blob(root)
    missing: list[str] = []
    for mod in modules:
        stem = Path(mod.replace(".", "/")).name
        token = re.escape(stem)
        if not re.search(token, blob, re.I) and mod not in blob:
            # also hypothesis/fast-check markers for that module
            if not re.search(r"hypothesis|fast.check|@given|property", blob, re.I):
                missing.append(
                    f"{mod}: no test reference — add tests/test_* mentioning "
                    f"'{stem}' (prefer Hypothesis/fast-check)"
                )
            elif not re.search(token, blob, re.I):
                missing.append(f"{mod}: property tests exist but module stem not referenced")
    if missing:
        return False, missing
    return True, [f"ok: {len(modules)} property_tests module(s) covered"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    ok, msgs = check(args.root.resolve())
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
