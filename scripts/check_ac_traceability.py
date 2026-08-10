#!/usr/bin/env python3
"""G1 — every AC-n in the linked spec must map to a real test (or N/A).

Fail closed for feature ships. Spec waiver (hotfix/chore/docs-only/prose-only) skips.

Usage::

  python3 scripts/check_ac_traceability.py --root . --pr-draft PR_DRAFT.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SPEC_RE = re.compile(r"\*\*Spec:\*\*\s*(\S+)", re.I)
WAIVER_RE = re.compile(
    r"\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)\b",
    re.I,
)
AC_RE = re.compile(r"\bAC-(\d+)\b", re.I)
TRACE_HEADER_RE = re.compile(r"^##\s+Traceability\b", re.I | re.M)
NA_RE = re.compile(r"AC-(\d+)\s*[:|].*\bN/?A\b", re.I)


def _acs_from_text(text: str) -> set[int]:
    return {int(m.group(1)) for m in AC_RE.finditer(text)}


def _trace_body(draft: str) -> str:
    m = re.search(r"##\s+Traceability\b(.*?)(?=\n## |\Z)", draft, re.I | re.S)
    return m.group(1) if m else ""


def _tests_corpus(root: Path) -> str:
    chunks: list[str] = []
    for base in (root / "tests", root / "scripts" / "tests"):
        if not base.is_dir():
            continue
        for p in base.rglob("test_*.py"):
            try:
                chunks.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
        for p in base.rglob("*_test.py"):
            try:
                chunks.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    # also scan pytest mark strings in any test file name mentioning ac
    return "\n".join(chunks)


def check(root: Path, pr_draft: Path) -> tuple[bool, list[str]]:
    root = root.resolve()
    msgs: list[str] = []
    if not pr_draft.is_file():
        return False, ["PR_DRAFT.md missing"]

    draft = pr_draft.read_text(encoding="utf-8", errors="replace")
    if WAIVER_RE.search(draft):
        return True, ["ok: Spec waiver — AC map skipped"]

    sm = SPEC_RE.search(draft)
    if not sm:
        return False, ["need **Spec:** path (or Spec waiver)"]

    spec_rel = sm.group(1).strip().strip("`")
    spec_path = (root / spec_rel).resolve()
    if not str(spec_path).startswith(str(root)):
        return False, [f"spec path escapes root: {spec_rel}"]
    if not spec_path.is_file():
        return False, [f"spec file missing: {spec_rel}"]

    spec_text = spec_path.read_text(encoding="utf-8", errors="replace")
    acs = _acs_from_text(spec_text)
    if not acs:
        return True, ["ok: no AC-n ids in spec — AC map N/A"]

    if not TRACE_HEADER_RE.search(draft):
        return False, ["## Traceability section required when spec has AC-n"]

    trace = _trace_body(draft)
    tests = _tests_corpus(root)
    # include draft traceability + PR for N/A rows
    corpus = tests + "\n" + draft

    missing: list[str] = []
    for n in sorted(acs):
        ac = f"AC-{n}"
        in_trace = bool(re.search(rf"\bAC-{n}\b", trace, re.I))
        na = bool(NA_RE.search(trace) and re.search(rf"AC-{n}", trace, re.I) and re.search(
            rf"AC-{n}[^\n]*N/?A", trace, re.I
        ))
        # test reference: AC-n string, test_ac_n, test_acn, mark ac-n
        in_test = bool(
            re.search(rf"\bAC-{n}\b", tests, re.I)
            or re.search(rf"\btest_ac_?{n}\b", tests, re.I)
            or re.search(rf"ac[_-]?{n}\b", tests, re.I)
        )
        if na:
            continue
        if not in_trace:
            missing.append(f"{ac}: not in ## Traceability")
        elif not in_test:
            missing.append(
                f"{ac}: no test reference (add test_ac_{n} / mention {ac} in tests/ "
                f"or Traceability row `{ac}: N/A — reason`)"
            )

    if missing:
        return False, missing
    return True, [f"ok: {len(acs)} AC(s) mapped"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    args = ap.parse_args(argv)
    root = args.root.resolve()
    draft = args.pr_draft or (root / "PR_DRAFT.md")
    ok, msgs = check(root, draft)
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
