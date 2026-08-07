#!/usr/bin/env python3
"""Gate: website/app products MUST have Playwright + Comet + e2e smoke (fail closed).

Opt out only with ``web_e2e.enabled: false`` in product_plugin.yaml.
Used by hard_gates, release_mgmt, bootstrap_check, and agent ship FSM.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from web_e2e_contract import validate_web_e2e  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--strict-surfaces",
        action="store_true",
        help="Deprecated: surfaces are mandatory by default (web_e2e.strict)",
    )
    ap.add_argument(
        "--lenient",
        action="store_true",
        help="Temporary migration: web_e2e.strict=false (surfaces/smoke warnings only)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    r = validate_web_e2e(root, strict=False if args.lenient else None)

    if args.json:
        print(json.dumps(r, indent=2))
    else:
        if not r.get("has_website"):
            print("⏭️  no website/app UI detected — web_e2e skipped (or enabled: false)")
            return 0
        print(f"website/app: yes ({', '.join(r.get('reasons') or [])})")
        print(f"strict={r.get('strict')} e2e_specs={r.get('e2e_spec_count')} "
              f"playwright_s_ids={len(r.get('playwright_s_ids') or [])}")
        for v in r.get("violations") or []:
            print(f"❌ {v}")
        for w in r.get("warnings") or []:
            print(f"⚠️  {w}")
        missing = r.get("missing_in_comet") or []
        if missing:
            print("missing_in_comet:", " ".join(missing[:20]))
        sc = r.get("scenarios") or []
        if sc:
            print("plugin surface IDs:", " ".join(x["global_id"] for x in sc))
        print("✅ check_web_e2e ok" if r.get("pass") else "❌ check_web_e2e failed (mandatory for web/app)")
    return 0 if r.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
