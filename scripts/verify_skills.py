#!/usr/bin/env python3
"""Audit skills for YAML frontmatter + required ship-chain presence.

Works in two layouts:
  - Harness repo:  skills/*/SKILL.md
  - Product repo:  .agents/skills/*/SKILL.md  (after install)

Exit 0 = ok · 1 = failures · 2 = skills dir missing (hard fail in product mode)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = {"name", "description"}

# Fallback if config/ship_skills.txt missing
DEFAULT_SHIP = (
    "spec",
    "execute_dev",
    "code_review",
    "cross_review",
    "behavior_validator",
    "pr_review",
    "release_mgmt",
    "sync_docs",
)


def _skills_root(repo: Path) -> Path | None:
    product = repo / ".agents" / "skills"
    harness = repo / "skills"
    # Harness source tree: prefer skills/ (SoT) over a possibly stale .agents/skills copy
    if (repo / "install_into_product.sh").is_file() and harness.is_dir() and any(
        harness.glob("*/SKILL.md")
    ):
        return harness
    if product.is_dir() and any(product.glob("*/SKILL.md")):
        return product
    if harness.is_dir() and any(harness.glob("*/SKILL.md")):
        return harness
    if product.is_dir():
        return product
    if harness.is_dir():
        return harness
    return None


def _load_ship_list(repo: Path) -> list[str]:
    candidates = [
        repo / "config" / "ship_skills.txt",
        repo / ".agents" / "policy" / "ship_skills.txt",
        Path(__file__).resolve().parent.parent / "config" / "ship_skills.txt",
    ]
    for p in candidates:
        if p.is_file():
            out: list[str] = []
            for line in p.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                out.append(s)
            if out:
                return out
    return list(DEFAULT_SHIP)


def _check_frontmatter(skill_md: Path, rel: str) -> list[str]:
    fails: list[str] = []
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        fails.append(f"{rel}: missing YAML frontmatter")
        return fails
    fm = m.group(1)
    for f in REQUIRED_FIELDS:
        if f"{f}:" not in fm:
            fails.append(f"{rel}: missing '{f}'")
    if "AGENT_REFERENCE" not in text and "base_constraints" not in text:
        # soft warning only — printed by caller
        pass
    return fails


def verify(repo: Path, *, require_ship: bool = True) -> int:
    root = _skills_root(repo)
    if root is None:
        print(f"❌ no skills directory under {repo} (expected skills/ or .agents/skills/)")
        return 2

    print(f"Skills root: {root}")
    fails = 0
    warns = 0
    skill_dirs = sorted({p.parent.name for p in root.glob("*/SKILL.md")})

    for name in skill_dirs:
        skill_md = root / name / "SKILL.md"
        rel = str(skill_md.relative_to(repo)) if skill_md.is_relative_to(repo) else str(skill_md)
        for msg in _check_frontmatter(skill_md, rel):
            print(f"❌ {msg}")
            fails += 1
        text = skill_md.read_text(encoding="utf-8")
        if "AGENT_REFERENCE" not in text and "base_constraints" not in text:
            print(f"⚠️  {rel}: no AGENT_REFERENCE / base_constraints citation")
            warns += 1

    if require_ship:
        ship = _load_ship_list(repo)
        missing = [s for s in ship if not (root / s / "SKILL.md").is_file()]
        if missing:
            print(f"❌ missing ship-chain skill(s): {', '.join(missing)}")
            fails += len(missing)
        else:
            print(f"✅ ship-chain skills present ({len(ship)}): {', '.join(ship)}")

    print(f"Skills found: {len(skill_dirs)}")
    if fails:
        print(f"❌ {fails} skill audit failure(s)")
        return 1
    print(f"✅ all skills valid ({warns} soft warning(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Harness or product root (default: cwd)",
    )
    ap.add_argument(
        "--no-require-ship",
        action="store_true",
        help="Skip ship-chain presence check",
    )
    args = ap.parse_args(argv)
    repo = Path(args.repo).resolve()
    return verify(repo, require_ship=not args.no_require_ship)


if __name__ == "__main__":
    sys.exit(main())
