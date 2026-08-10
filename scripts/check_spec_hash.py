#!/usr/bin/env python3
"""G2 — linked Spec path must exist; optional spec_sha256 must match."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

SPEC_RE = re.compile(r"\*\*Spec:\*\*\s*(\S+)", re.I)
SHA_RE = re.compile(r"\*\*spec_sha256:\*\*\s*([a-fA-F0-9]{64})\b|spec_sha256:\s*([a-fA-F0-9]{64})\b", re.I)
WAIVER_RE = re.compile(r"\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)\b", re.I)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def check(root: Path, pr_draft: Path) -> tuple[bool, list[str]]:
    root = root.resolve()
    if not pr_draft.is_file():
        return False, ["PR_DRAFT.md missing"]
    text = pr_draft.read_text(encoding="utf-8", errors="replace")
    if WAIVER_RE.search(text):
        return True, ["ok: Spec waiver — hash skipped"]
    sm = SPEC_RE.search(text)
    if not sm:
        return False, ["need **Spec:** path or Spec waiver"]
    rel = sm.group(1).strip().strip("`")
    path = (root / rel).resolve()
    if not str(path).startswith(str(root)) or not path.is_file():
        return False, [f"spec missing or escapes root: {rel}"]
    digest = file_sha256(path)
    hm = SHA_RE.search(text)
    if hm:
        want = (hm.group(1) or hm.group(2) or "").lower()
        if want != digest.lower():
            return False, [f"spec_sha256 mismatch: draft={want[:12]}… file={digest[:12]}…"]
        return True, [f"ok: spec_sha256 matches ({digest[:12]}…)"]
    return True, [f"ok: spec present (sha256={digest[:12]}…; pin with spec_sha256: optional)"]


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
