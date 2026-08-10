#!/usr/bin/env python3
"""G3 — changed non-test source modules need a test reference or untested waiver.

Usage::

  python3 scripts/check_changed_path_tests.py --base HEAD~1 --head HEAD --pr-draft PR_DRAFT.md
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SRC_SUFFIX = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}
SKIP_PARTS = (
    "tests/",
    "test/",
    "fixtures/",
    "testdata/",
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
    "migrations/",
)


def _changed(repo: Path, base: str, head: str) -> list[str]:
    for sep in ("...", ".."):
        r = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}{sep}{head}"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode == 0:
            return [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    return []


def _is_product_src(rel: str) -> bool:
    p = rel.replace("\\", "/")
    if any(s in p for s in SKIP_PARTS):
        return False
    if p.startswith("test_") or "/test_" in p:
        return False
    suf = Path(p).suffix.lower()
    if suf not in SRC_SUFFIX:
        return False
    # scripts tools and product src
    return True


def _stem_tokens(rel: str) -> list[str]:
    stem = Path(rel).stem
    parts = re.split(r"[_\-.]", stem)
    return [x for x in parts if len(x) >= 3]


def _tests_blob(repo: Path) -> str:
    chunks: list[str] = []
    for base in (repo / "tests", repo / "scripts" / "tests"):
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            try:
                chunks.append(p.read_text(encoding="utf-8", errors="replace"))
                chunks.append(str(p))
            except OSError:
                continue
    return "\n".join(chunks)


def _untested_waivers(draft: str) -> set[str]:
    m = re.search(
        r"##\s+Untested paths\b(.*?)(?=\n## |\Z)",
        draft,
        re.I | re.S,
    )
    if not m:
        return set()
    body = m.group(1)
    found: set[str] = set()
    for line in body.splitlines():
        line = line.strip().strip("|").strip()
        if not line or line.startswith("---") or line.lower().startswith("path"):
            continue
        # first path-like token
        tok = re.search(r"[\w./\-]+\.(py|ts|tsx|js|jsx|go|rs)\b", line)
        if tok:
            found.add(tok.group(0).lstrip("./"))
    return found


def check(
    repo: Path,
    base: str,
    head: str,
    pr_draft: Path | None,
) -> tuple[bool, list[str]]:
    repo = repo.resolve()
    changed = [c for c in _changed(repo, base, head) if _is_product_src(c)]
    if not changed:
        return True, ["ok: no product source files in diff"]

    draft = ""
    if pr_draft and pr_draft.is_file():
        draft = pr_draft.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\*\*Spec waiver:\*\*\s*(docs-only|prose-only)\b", draft, re.I):
        return True, ["ok: docs/prose waiver — path tests skipped"]

    waivers = _untested_waivers(draft)
    tests = _tests_blob(repo)
    missing: list[str] = []
    for rel in changed:
        if rel in waivers or rel.lstrip("./") in waivers:
            continue
        stem = Path(rel).stem
        tokens = _stem_tokens(rel)
        hit = stem in tests or rel in tests
        if not hit:
            for t in tokens:
                if re.search(rf"\b{re.escape(t)}\b", tests, re.I):
                    hit = True
                    break
        if not hit:
            missing.append(
                f"{rel}: no test reference — add tests mentioning module "
                f"or ## Untested paths row with reason"
            )
    if missing:
        return False, missing
    return True, [f"ok: {len(changed)} source path(s) covered or waived"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--pr-draft", type=Path, default=None)
    args = ap.parse_args(argv)
    root = args.repo.resolve()
    draft = args.pr_draft or (root / "PR_DRAFT.md")
    ok, msgs = check(root, args.base, args.head, draft)
    for m in msgs:
        print(("✅ " if ok else "❌ ") + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
