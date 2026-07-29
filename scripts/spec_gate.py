#!/usr/bin/env python3
"""Spec gate for /execute_dev — require Spec path or Spec waiver before code work.

Exit 0 = ok; 1 = blocked.
Reads PR_DRAFT.md and optional pipeline.json fields (spec_id, waiver).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SPEC_RE = re.compile(r"\*\*Spec:\*\*\s*(\S+)", re.I)
WAIVER_RE = re.compile(
    r"\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)\b",
    re.I,
)
WAIVERS = frozenset({"hotfix", "chore", "docs-only", "prose-only"})


def _pipeline(root: Path) -> dict:
    p = root / ".agents" / "state" / "pipeline.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def check(root: Path, *, pr_draft: Path | None = None, allow_missing_draft: bool = False) -> tuple[bool, list[str]]:
    """Return (ok, messages)."""
    root = Path(root).resolve()
    draft_path = pr_draft or (root / "PR_DRAFT.md")
    msgs: list[str] = []
    draft = ""
    if draft_path.is_file():
        draft = draft_path.read_text(encoding="utf-8", errors="replace")
    elif not allow_missing_draft:
        # pipeline-only path still allowed
        pass

    pipe = _pipeline(root)
    waiver = (pipe.get("waiver") or "").strip().lower()
    spec_id = (pipe.get("spec_id") or "").strip()

    m = SPEC_RE.search(draft)
    w = WAIVER_RE.search(draft)
    if w:
        waiver = w.group(1).lower()
    if m:
        spec_id = m.group(1).strip().strip("`")

    if waiver in WAIVERS:
        msgs.append(f"ok: Spec waiver={waiver}")
        return True, msgs

    if spec_id:
        # Relative to product root
        cand = root / spec_id
        if cand.is_file():
            msgs.append(f"ok: Spec file {spec_id}")
            return True, msgs
        # also try as-is path
        if Path(spec_id).is_file():
            msgs.append(f"ok: Spec file {spec_id}")
            return True, msgs
        msgs.append(f"fail: Spec path not found: {spec_id}")
        return False, msgs

    msgs.append(
        "fail: need **Spec:** <path> in PR_DRAFT or pipeline spec_id, "
        "or **Spec waiver:** hotfix|chore|docs-only|prose-only"
    )
    return False, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    ap.add_argument(
        "--allow-missing-draft",
        action="store_true",
        help="Allow pipeline-only spec_id/waiver without PR_DRAFT",
    )
    args = ap.parse_args(argv)
    ok, msgs = check(
        args.root,
        pr_draft=args.pr_draft,
        allow_missing_draft=args.allow_missing_draft,
    )
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m if not m.startswith("ok:") and not m.startswith("fail:") else ("✅ " + m[4:] if m.startswith("ok:") else "❌ " + m[6:]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
