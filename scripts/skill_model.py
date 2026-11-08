#!/usr/bin/env python3
"""Resolve the model a ship step must run under, from the skill's own frontmatter.

Design (dispatch-level pinning): a skill cannot switch its own model mid-session — Grok CLI takes `-m`
at launch and Hermes only has a session-level override. So the dispatcher reads the declaration and
launches the step with it, and the declaration is recorded in the build log.

Reversible by design:
  * SKILL_MODEL_PIN=0  -> everything behaves as before (dispatcher default), no frontmatter consulted.
  * no `model:` key    -> same, unpinned.
  * unknown/unavailable model -> exit 2, fail closed, no silent fallback.

    python3 scripts/skill_model.py --skill spec --root .
    -> {"skill": "spec", "model": "grok-4.7", "reasoning_effort": "high", "pinned": true}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Models the dispatchers can actually launch. Anything else fails closed.
ALLOWED = {"grok-4.7", "deepseek-flash", "deepseek-v4-pro"}
DETERMINISTIC = "none"


def frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            if " " not in key.strip():
                out[key.strip()] = value.strip().strip("\"'")
    return out


def skill_file(root: Path, skill: str) -> Path:
    for base in (root / ".agents" / "skills", root / "skills"):
        candidate = base / skill / "SKILL.md"
        if candidate.is_file():
            return candidate
    return root / ".agents" / "skills" / skill / "SKILL.md"


def resolve(root: Path, skill: str) -> dict:
    if os.environ.get("SKILL_MODEL_PIN", "1") == "0":
        return {"skill": skill, "model": None, "reasoning_effort": None, "pinned": False,
                "reason": "SKILL_MODEL_PIN=0"}
    meta = frontmatter(skill_file(root, skill))
    model = (meta.get("model") or "").strip()
    effort = (meta.get("reasoning_effort") or "").strip() or None
    if not model:
        return {"skill": skill, "model": None, "reasoning_effort": effort, "pinned": False,
                "reason": "no model declared"}
    if model == DETERMINISTIC:
        return {"skill": skill, "model": None, "reasoning_effort": None, "pinned": False,
                "deterministic": True, "reason": "declared deterministic (no model step)"}
    if model not in ALLOWED:
        raise SystemExit(f"skill_model: {skill} declares unavailable model {model!r}; allowed: {sorted(ALLOWED)}")
    return {"skill": skill, "model": model, "reasoning_effort": effort, "pinned": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    print(json.dumps(resolve(Path(args.root), args.skill), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
