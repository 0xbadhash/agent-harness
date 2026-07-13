#!/usr/bin/env python3
"""Bundle generator. Reads BUNDLE_MANIFEST and emits ALL_PRINCIPLES.md."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ALL_PRINCIPLES.md"
AUDIT = ROOT / "logs" / "token_audit.log"

BUNDLE_MANIFEST: dict[str, dict[str, Any]] = {
    "slim-dev": {
        "target_tokens": 15000,
        "files": [
            ".agents/base_constraints.md",
            "GEMINI.md",
            "ENGINEERING_ASSURANCE.md",
            "BACKEND_ROADMAP.md",
            "docs/PRODUCT.md",
            "docs/TESTING.md",
            "migration/src/README.md",
            "scripts/validate.py",
            "scripts/scaffold_tests.py",
            "scripts/compliance_engine.py",
            ".agents/skills/execute_dev/SKILL.md",
        ],
    },
    "slim": {
        "target_tokens": 30000,
        "files": [
            "GEMINI.md", "ENGINEERING_ASSURANCE.md", "WORKFLOW_DOCUMENTATION.md",
            "CONTRIBUTING.md", "BACKEND_ROADMAP.md",
            "PRODUCTION_GAP_ANALYSIS.md", "docs/AGENT_REFERENCE.md",
            "docs/RISK_SCORING.md", "docs/MATE_OBSERVABILITY.md",
            "docs/TESTING.md",
            "docs/ARCHITECTURE.md", "docs/PRODUCT.md", "docs/SECURITY.md",
            "docs/PRODUCT_BOUNDARY.md",
            "migration/src/README.md",
            "scripts/validate.py", "scripts/scaffold_tests.py",
            "scripts/compliance_engine.py", "scripts/pipeline_state.py",
            "scripts/check_repo_hygiene.py",
            ".agents/skills/execute_dev/SKILL.md",
            ".agents/README.md",
        ],
    },
    "full": {"target_tokens": 50000, "files": ["**/*"]},  # everything
}

def _collect(mode: str) -> list[Path]:
    spec = BUNDLE_MANIFEST[mode]
    if mode == "full":
        return sorted(p for p in ROOT.rglob("*") if p.is_file()
                      and ".git" not in p.parts and p.name != "ALL_PRINCIPLES.md")
    files: list[str] = spec["files"]
    return [ROOT / f for f in files if (ROOT / f).exists()]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=sorted(BUNDLE_MANIFEST), default="slim-dev")
    ap.add_argument("--check", action="store_true", help="CI gate: fail if bundle stale")
    args = ap.parse_args()

    files = _collect(args.mode)
    parts = [f"# 🧬 ALL PRINCIPLES — mode={args.mode}\n",
             f"_Generated {datetime.now(timezone.utc).isoformat()}_\n\n"]
    total_bytes = 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = p.relative_to(ROOT)
        parts.append(f"\n---\n## 📄 {rel}\n```\n{text}\n```\n")
        total_bytes += len(text.encode("utf-8"))

    OUT.write_text("".join(parts), encoding="utf-8")
    est_tokens = total_bytes // 4

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode, "bytes": total_bytes, "est_tokens": est_tokens,
        }) + "\n")

    print(f"✅ bundle written: {OUT} ({total_bytes} bytes, ~{est_tokens} tokens)")
    if args.check:
        target = BUNDLE_MANIFEST[args.mode]["target_tokens"]
        if est_tokens > target * 1.2:
            print(f"⚠️  over target ({target})")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
