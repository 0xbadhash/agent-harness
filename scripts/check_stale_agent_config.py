#!/usr/bin/env python3
"""Fail closed if agent-config names missing files, skills, or commands.

Scans AGENTS.md, skill SKILL.md, product_plugin.yaml, config/ship_skills.txt,
and next_skill known routes. Does not invent a new skill.

  python3 scripts/check_stale_agent_config.py --root .
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PATH_RE = re.compile(
    r"(?:^|[\s`\"'(])((?:scripts|bin)/[A-Za-z0-9_./-]+\.(?:py|sh))",
)
CMD_RE = re.compile(
    r"(?:python3|python|bash)\s+(scripts/[A-Za-z0-9_./-]+\.(?:py|sh))",
)

SKIP_SUBSTRINGS = (
    "your-product",
    "my-feature",
    "<slug>",
    "example",
    "e.g.",
)


def _skill_dirs(root: Path) -> set[str]:
    names: set[str] = set()
    for base in (root / "skills", root / ".agents" / "skills"):
        if not base.is_dir():
            continue
        for p in base.iterdir():
            if p.is_dir() and (p / "SKILL.md").is_file():
                names.add(p.name)
    return names


def _scan_text(rel: str, text: str, root: Path, missing: list[str]) -> None:
    for rx in (PATH_RE, CMD_RE):
        for m in rx.finditer(text):
            raw = m.group(1).strip().strip("`")
            ctx = text[max(0, m.start() - 80) : m.end() + 40].lower()
            if any(s in raw.lower() or s in ctx for s in SKIP_SUBSTRINGS):
                continue
            if "<" in raw or "{" in raw:
                continue
            # Portfolio runner lives in harness SoT bin/; products often omit it
            if raw.startswith("bin/") and not (root / "bin").is_dir():
                continue
            # Outputs / optional local files are not required to exist
            if raw.startswith(".agents/artifacts/") or "/artifacts/" in raw:
                continue

            if raw.endswith("CONSTITUTION.md"):
                continue
            if "writes:" in ctx or "write " in ctx or "optional" in ctx or "if exists" in ctx:
                continue
            if raw.startswith(".agents/policy/") and "TEST_MATRIX" in raw:
                continue
            p = root / raw
            if not p.exists():
                missing.append(f"{rel}: missing `{raw}`")


def check(root: Path) -> tuple[bool, list[str]]:
    root = root.resolve()
    missing: list[str] = []
    ok_notes: list[str] = []
    has_agent_config = (
        (root / "AGENTS.md").is_file()
        or (root / "config" / "ship_skills.txt").is_file()
        or (root / "skills").is_dir()
        or (root / ".agents" / "skills").is_dir()
    )
    if not has_agent_config:
        return True, ["ok: no agent-config to scan"]


    # ship_skills SoT (ignore product-local policy copies of removed skills)
    skills = _skill_dirs(root)
    removed: set[str] = set()
    rem_f = root / "config" / "removed_portable_skills.txt"
    if rem_f.is_file():
        for line in rem_f.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                removed.add(line)
    ship_list = root / "config" / "ship_skills.txt"
    if ship_list.is_file():
        for line in ship_list.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or line in removed:
                continue
            if line not in skills:
                missing.append(f"{ship_list.relative_to(root)}: skill `{line}` not on disk")

    scan_files: list[Path] = []
    for rel in ("AGENTS.md",):
        p = root / rel
        if p.is_file():
            scan_files.append(p)
    # Harness SoT skills/ only (installed copies under .agents/skills duplicate)
    if (root / "skills").is_dir():
        scan_files.extend((root / "skills").glob("*/SKILL.md"))
    elif (root / ".agents" / "skills").is_dir():
        scan_files.extend((root / ".agents" / "skills").glob("*/SKILL.md"))

    plugin = root / ".agents" / "product_plugin.yaml"
    if plugin.is_file():
        scan_files.append(plugin)

    for path in scan_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        _scan_text(rel, text, root, missing)

    # next_skill.py exists (router SoT)
    if not (root / "scripts" / "next_skill.py").is_file():
        missing.append("scripts/next_skill.py missing")


    if missing:
        # cap noise
        uniq = sorted(set(missing))
        return False, [f"fail: {m}" for m in uniq[:40]]
    ok_notes.append("ok: agent-config refs resolve (files/skills/commands)")
    return True, ok_notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args(argv)
    ok, msgs = check(args.root.resolve())
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    print("✅ check_stale_agent_config ok" if ok else "❌ check_stale_agent_config FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
