#!/usr/bin/env python3
"""Detects doc-boundary violations via git diff. Flags content placed in wrong files."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Doc boundaries enforced per canonical routing doc (GEMINI.md). Keywords that should NOT appear.
BOUNDARIES = {
    "ENGINEERING_ASSURANCE.md": {"forbid": ["example", "how to", "tutorial", "step-by-step"]},
    "WORKFLOW_DOCUMENTATION.md": {"forbid": ["policy:", "rule:", "must always"]},
    "CONTRIBUTING.md": {"forbid": ["policy:", "architecture decision"]},
    "docs/TESTING.md": {"forbid": ["security threat", "architecture diagram"]},
    "docs/ARCHITECTURE.md": {"forbid": ["test strategy", "onboarding"]},
    "docs/SECURITY.md": {"forbid": ["test strategy", "onboarding"]},
}

def _diff_files(diff: str | None) -> list[str]:
    if not diff:
        return []
    r = subprocess.run(["git", "diff", "--name-only", diff], cwd=ROOT, capture_output=True, text=True)
    return [f for f in r.stdout.splitlines() if f.strip()]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", help="Git range")
    args = ap.parse_args()

    changed = _diff_files(args.diff)
    violations = 0
    for f in changed:
        for doc, rules in BOUNDARIES.items():
            if not f.endswith(doc):
                continue
            text = (ROOT / f).read_text(encoding="utf-8", errors="ignore").lower()
            for kw in rules["forbid"]:
                if kw in text:
                    print(f"⚠️  DRIFT: {f} contains '{kw}' (out of scope)")
                    violations += 1
    if violations:
        print(f"❌ {violations} drift violation(s)")
        return 1
    print("✅ no drift detected")
    return 0

if __name__ == "__main__":
    sys.exit(main())
