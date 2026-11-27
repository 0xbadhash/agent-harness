#!/usr/bin/env python3
"""Markdown escape-hatch audit: prose cannot replace a check.

Rules:

- ``AGENTS.md`` is capped at 250 lines; growth past the cap fails.
- A rule bullet that says ``for now``, ``temporary``, ``works around``, or
  ``safe to ignore`` must name the check that bounds it.
- Every bullet under a ``## Do not`` heading must name an enforcing check
  (``scripts/…``, ``tests/…``, ``/pr_review``, ``next_skill``, ``pipeline_state``,
  or an exit code). Prose-only prohibitions are unenforced and fail.

Usage::

  python3 scripts/check_markdown_audit.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_CAP = 250
RULE_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\S")
DO_NOT_RE = re.compile(r"^##\s+Do not\b", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
JUSTIFY_RE = re.compile(
    r"\b(for now|temporar(?:y|ily)|works? around|safe to ignore|just in case)\b",
    re.IGNORECASE,
)
ENFORCE_RE = re.compile(
    r"(check[:_-]|scripts/[\w./-]+|tests?/[\w./-]+|test_[\w]+\.py|"
    r"/pr_review|next_skill|pipeline_state|exit(?:\s+code)?(?:\s+is)?\s+[1-9])",
    re.IGNORECASE,
)


def check_agents_bloat(root: Path, max_lines: int = AGENTS_CAP) -> tuple[bool, list[str]]:
    """Return (ok, messages): AGENTS.md may not grow past the cap."""
    agents = Path(root) / "AGENTS.md"
    if not agents.is_file():
        return True, ["ok: no AGENTS.md"]
    count = len(agents.read_text(encoding="utf-8", errors="replace").splitlines())
    if count > max_lines:
        return False, [
            f"fail: AGENTS.md is {count} lines (cap {max_lines}) — move rules into "
            "a check or a skill"
        ]
    return True, [f"ok: AGENTS.md {count}/{max_lines} lines"]


def _markdown_files(root: Path) -> list[Path]:
    root = Path(root)
    files: list[Path] = []
    agents = root / "AGENTS.md"
    if agents.is_file():
        files.append(agents)
    for base in (root / "skills", root / ".agents" / "skills"):
        if not base.is_dir():
            continue
        files.extend(p for p in base.glob("*/SKILL.md") if p.is_file())
        # Harness SoT wins; installed copies under .agents duplicate it
        if base.name == "skills" and (root / "skills").is_dir():
            break
    templates = root / "templates"
    if templates.is_dir():
        files.extend(p for p in templates.glob("*.md") if p.is_file())
    return sorted(set(files))


def scan_markdown(path: Path, root: Path) -> list[str]:
    findings: list[str] = []
    rel = path.relative_to(root).as_posix()
    in_fence = False
    in_do_not = False
    for number, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
    ):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if HEADING_RE.match(line):
            in_do_not = bool(DO_NOT_RE.match(line))
            continue
        if not RULE_RE.match(line):
            continue
        has_check = bool(ENFORCE_RE.search(line))
        if JUSTIFY_RE.search(line) and not has_check:
            findings.append(
                f"{rel}:{number}: escape_hatch: prose justifies skipping a check: "
                + line.strip()[:160]
            )
        if in_do_not and not has_check:
            findings.append(
                f"{rel}:{number}: unenforced: `Do not` bullet names no check: "
                + line.strip()[:160]
            )
    return findings


def check(root: Path) -> tuple[bool, list[str]]:
    """Return (ok, messages) for validate/hard_gates."""
    root = Path(root)
    messages: list[str] = []
    fails = 0

    ok, bloat_msgs = check_agents_bloat(root)
    if not ok:
        messages.extend(bloat_msgs)
        fails += 1

    findings: list[str] = []
    for path in _markdown_files(root):
        findings.extend(scan_markdown(path, root))
    for finding in findings:
        messages.append("fail: " + finding)
        fails += 1

    if fails:
        messages.append(f"{fails} markdown finding(s)")
        return False, messages
    notes = [] if not ok and bloat_msgs == ["ok: no AGENTS.md"] else bloat_msgs
    return True, notes + ["ok: markdown escape-hatch audit"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    ok, messages = check(args.root.resolve())
    for message in messages:
        print(("✅ " if ok else "❌ ") + message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
