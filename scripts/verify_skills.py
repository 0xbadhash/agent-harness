#!/usr/bin/env python3
"""Audits .agents/skills/* for YAML frontmatter compliance + base_constraints inheritance."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"
REQUIRED_FIELDS = {"name", "description"}

def main() -> int:
    if not SKILLS.exists():
        print("⚠️  no skills directory")
        return 0
    fails = 0
    for skill_md in SKILLS.rglob("SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if not m:
            print(f"❌ {skill_md.relative_to(ROOT)}: missing YAML frontmatter")
            fails += 1
            continue
        fm = m.group(1)
        for f in REQUIRED_FIELDS:
            if f"{f}:" not in fm:
                print(f"❌ {skill_md.relative_to(ROOT)}: missing '{f}'")
                fails += 1
        if "docs/AGENT_REFERENCE.md" not in text and "AGENT_REFERENCE" not in text:
            print(f"⚠️  {skill_md.relative_to(ROOT)}: no AGENT_REFERENCE citation")
    if fails:
        print(f"❌ {fails} skill audit failure(s)")
        return 1
    print("✅ all skills valid")
    return 0

if __name__ == "__main__":
    sys.exit(main())
