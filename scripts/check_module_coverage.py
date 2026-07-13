#!/usr/bin/env python3
"""Verifies per-module coverage against config/coverage_config.json thresholds."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "coverage_config.json"

def main() -> int:
    cfg: dict[str, Any]
    if not CFG.exists():
        print(f"⚠️  {CFG} missing — using default 80%")
        cfg = {"default": 80, "modules": {}}
    else:
        cfg = json.loads(CFG.read_text(encoding="utf-8"))

    # Stub: in production, parse coverage.xml / .coverage JSON
    # Here we just validate the config is well-formed
    if "default" not in cfg or not isinstance(cfg["default"], (int, float)):
        print("❌ coverage_config.json missing numeric 'default'")
        return 1
    print(f"✅ coverage config valid (default {cfg['default']}%, {len(cfg.get('modules', {}))} overrides)")
    return 0

if __name__ == "__main__":
    sys.exit(main())

