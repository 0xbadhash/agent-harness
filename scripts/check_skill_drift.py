#!/usr/bin/env python3
"""Fail when the install copy of a skill drifts from skills/.

skills/ is the source. .agents/skills/ is a generated install target.
A missing install tree is success when skills/ already contains every
ship and optional name (fresh clone, no install step).

Prints one problem per line:
  DIFF <skill>     install file bytes differ from skills/<skill>
  MISSING <skill>  required name has no install SKILL.md (or, when the
                   install tree is absent, skills/ lacks that SKILL.md)
  EXTRA <skill>    .agents/skills/<skill> exists and skills/ does not

Success prints ``skill drift ok`` and exits 0.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _names(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s.split()[0])
    return out


def _required(root: Path) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for rel in ("config/ship_skills.txt", "config/optional_skills.txt"):
        for name in _names(root / rel):
            if name not in seen:
                seen.add(name)
                names.append(name)
    return names


def _files(skill_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not skill_dir.is_dir():
        return found
    for path in skill_dir.rglob("*"):
        if path.is_file():
            found[path.relative_to(skill_dir).as_posix()] = path
    return found


def _differs(install_skill: Path, source_skill: Path) -> bool:
    install_files = _files(install_skill)
    for rel, inst in install_files.items():
        src = source_skill / rel
        if not src.is_file():
            return True
        if inst.read_bytes() != src.read_bytes():
            return True
    return False


def problems_for(root: Path) -> list[str]:
    skills = root / "skills"
    install = root / ".agents" / "skills"
    required = _required(root)
    problems: list[str] = []
    if not install.is_dir():
        for name in required:
            if not (skills / name / "SKILL.md").is_file():
                problems.append(f"MISSING {name}")
        return problems

    source_dirs = {p.name for p in skills.iterdir() if p.is_dir()} if skills.is_dir() else set()
    install_dirs = {p.name for p in install.iterdir() if p.is_dir()}
    for name in sorted(install_dirs - source_dirs):
        problems.append(f"EXTRA {name}")
    for name in sorted(install_dirs & source_dirs):
        if _differs(install / name, skills / name):
            problems.append(f"DIFF {name}")
    for name in required:
        if not (install / name / "SKILL.md").is_file():
            problems.append(f"MISSING {name}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args(argv)
    root = args.root.expanduser().resolve()
    found = problems_for(root)
    if found:
        print("\n".join(found))
        return 1
    print("skill drift ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
