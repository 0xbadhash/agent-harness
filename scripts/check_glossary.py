#!/usr/bin/env python3
"""Validate the glossary artifact: complete rows and no normalized collisions.

A repo without a glossary file (``GLOSSARY.md``, ``docs/GLOSSARY.md``, or
``docs/glossary.md``) skips with a stated reason. A table row must carry a term,
a definition, and an owning surface; two rows must not normalize to the same
term. Bullet entries keep the older term-only shape and are not checked for the
two extra cells.

Usage::

  python3 scripts/check_glossary.py --root .
  python3 scripts/check_glossary.py --root . --json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from spec_gate import GLOSSARY_PATHS, check_glossary_collisions  # noqa: E402

REQUIRED_CELLS = 3


@dataclass
class Report:
    path: Path | None = None
    terms: int = 0
    findings: list[str] = field(default_factory=list)
    skip: str | None = None

    @property
    def ok(self) -> bool:
        return not self.findings


def _first_glossary(root: Path) -> Path | None:
    for rel in GLOSSARY_PATHS:
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return None


def _table_rows(path: Path) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        row = line.strip()
        if not row.startswith("|") or row.startswith("|---"):
            continue
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if cells and cells[0].lower() == "term":
            continue
        rows.append((number, cells))
    return rows


def check(root: Path) -> Report:
    root = Path(root)
    path = _first_glossary(root)
    if path is None:
        return Report(skip="no glossary file")
    rows = _table_rows(path)
    findings: list[str] = []
    for number, cells in rows:
        if not cells or not cells[0]:
            findings.append(f"{path.name}:{number}: empty term")
            continue
        if len(cells) < REQUIRED_CELLS or not all(cells[:REQUIRED_CELLS]):
            findings.append(
                f"{path.name}:{number}: term {cells[0]!r} needs a definition "
                "and an owning surface"
            )
    ok, messages = check_glossary_collisions(root)
    if not ok:
        findings.extend(messages)
    return Report(path=path, terms=len(rows), findings=findings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = check(args.root)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "skip": report.skip,
                    "path": str(report.path) if report.path else None,
                    "terms": report.terms,
                    "findings": report.findings,
                },
                indent=2,
            )
        )
    elif report.skip:
        print(f"skip: {report.skip}")
    elif report.ok:
        name = report.path.name if report.path is not None else "(unknown)"
        print(f"ok: {report.terms} glossary term(s) in {name}")
    else:
        for finding in report.findings:
            print(f"fail: {finding}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
