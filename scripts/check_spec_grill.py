#!/usr/bin/env python3
"""Fail-closed check: linked Spec files must include grill-me evidence.

Feature specs (non-waiver) need ``## Grill-me`` with either:
  - **Status:** complete (or complete equivalent) and ≥3 answered Q/A pairs, or
  - **Status:** spike-skipped with a reason ≥20 characters.

Usage::

  python3 scripts/check_spec_grill.py --root .
  python3 scripts/check_spec_grill.py --spec path/to/spec.md
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
GRILL_HEADER_RE = re.compile(r"^##\s+Grill-me\b", re.I | re.M)
STATUS_RE = re.compile(
    r"\*\*Status:\*\*\s*(complete|done|ok|spike-skipped|skipped)\b",
    re.I,
)
REASON_RE = re.compile(r"\*\*Reason:\*\*\s*(.+)", re.I)
# Q/A pair: line with Q: and later A: in section
QA_RE = re.compile(
    r"^\s*[-*]?\s*Q:\s*\S.+$",
    re.I | re.M,
)
ANS_RE = re.compile(
    r"^\s*[-*]?\s*A:\s*\S.+$",
    re.I | re.M,
)


def _grill_section(text: str) -> str:
    m = re.search(
        r"^##\s+Grill-me\b(.*?)(?=^##\s|\Z)",
        text,
        re.I | re.M | re.S,
    )
    return m.group(1) if m else ""


def check_spec_text(text: str, *, label: str = "spec") -> tuple[bool, list[str]]:
    """Return (ok, messages) for a single spec body."""
    msgs: list[str] = []
    if not GRILL_HEADER_RE.search(text):
        return False, [f"{label}: missing ## Grill-me section"]

    body = _grill_section(text)
    sm = STATUS_RE.search(body) or STATUS_RE.search(text)
    status = (sm.group(1).lower() if sm else "").strip()

    if status in {"spike-skipped", "skipped"}:
        rm = REASON_RE.search(body)
        reason = (rm.group(1).strip() if rm else "")
        if len(reason) < 20:
            return False, [
                f"{label}: spike-skipped requires **Reason:** ≥20 characters"
            ]
        return True, [f"ok: {label} grill spike-skipped"]

    # complete path (status optional if enough Q/A)
    qs = QA_RE.findall(body)
    ans = ANS_RE.findall(body)
    n = min(len(qs), len(ans))
    if n < 3:
        return False, [
            f"{label}: grill-me needs ≥3 Q/A pairs (found Q={len(qs)} A={len(ans)}); "
            "or **Status:** spike-skipped with Reason"
        ]
    if status and status not in {"complete", "done", "ok"}:
        msgs.append(f"warn: {label} grill Status={status!r} (expected complete)")
    return True, [f"ok: {label} grill-me complete ({n} Q/A)"] + msgs


def check_path(path: Path) -> tuple[bool, list[str]]:
    if not path.is_file():
        return False, [f"spec missing: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return check_spec_text(text, label=str(path))


def check_from_pr_draft(root: Path, pr_draft: Path) -> tuple[bool, list[str]]:
    root = root.resolve()
    if not pr_draft.is_file():
        return True, ["ok: no PR_DRAFT — grill check N/A"]
    draft = pr_draft.read_text(encoding="utf-8", errors="replace")
    if WAIVER_RE.search(draft):
        return True, ["ok: Spec waiver — grill check skipped"]
    sm = SPEC_RE.search(draft)
    if not sm:
        return True, ["ok: no **Spec:** path — grill check N/A (spec_gate owns missing Spec)"]
    rel = sm.group(1).strip().strip("`")
    path = (root / rel).resolve()
    if not str(path).startswith(str(root)):
        return False, [f"spec path escapes root: {rel}"]
    return check_path(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    ap.add_argument("--spec", type=Path, default=None, help="Check one spec file")
    args = ap.parse_args(argv)
    root = args.root.resolve()

    if args.spec:
        ok, msgs = check_path(args.spec if args.spec.is_absolute() else root / args.spec)
    else:
        draft = args.pr_draft or (root / "PR_DRAFT.md")
        ok, msgs = check_from_pr_draft(root, draft)

    for m in msgs:
        print(("✅ " if ok and m.startswith("ok:") else ("⚠️  " if m.startswith("warn:") else ("✅ " if ok else "❌ "))) + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
