#!/usr/bin/env python3
"""Sync product copies of ``scripts/vault_schema_lint.py`` from the harness SoT.

Canonical copy: ``<agent-harness>/scripts/vault_schema_lint.py`` (this repo).
Targets: every repo in ``config/night_shift_products.yaml`` (or ``--products-file``
/ ``$NIGHT_SHIFT_PRODUCTS_FILE``), plus any ``--root`` given explicitly.

Modes:
  --check   (default) report drift table with sha256; exit 1 if any copy drifts.
  --write   copy the canonical file over drifted copies (idempotent: identical
            copies are left untouched, mtime included).
  --commit  with --write: ``git commit --only`` just the lint file in each repo
            that changed. Refuses (lists as STUCK) repos with staged changes,
            an in-progress merge/rebase, an index.lock, or a dirty lint file
            that differs from both old HEAD and canonical.
  --skip ID repeatable; leave that product untouched (e.g. lock hold) → STUCK.

Never pushes. Never edits anything but ``scripts/vault_schema_lint.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HARNESS_ROOT = Path(__file__).resolve().parent.parent
REL = Path("scripts") / "vault_schema_lint.py"
CANONICAL = HARNESS_ROOT / REL
DEFAULT_MSG = (
    "chore(harness): sync vault_schema_lint from agent-harness SoT\n\n"
    "Byte-identical copy of agent-harness scripts/vault_schema_lint.py "
    "(sha256 {sha}). Brings the surface-alias fix (ui -> catalyxt-ds) that\n"
    "stale copies lack. Only this file changes. Synced by "
    "scripts/sync_vault_schema_lint.py."
)


def sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def load_products(path: Path | None) -> list[tuple[str, Path]]:
    if path is None:
        env = os.environ.get("NIGHT_SHIFT_PRODUCTS_FILE")
        path = Path(env) if env else HARNESS_ROOT / "config" / "night_shift_products.yaml"
    rows: list[tuple[str, Path]] = []
    if not path.is_file():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        line = line.lstrip("-").strip()
        pid, proot = line.split(":", 1)
        rows.append((pid.strip(), Path(proot.strip().strip("\"'")).expanduser()))
    return rows


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def commit_blockers(root: Path) -> list[str]:
    """Reasons a lint-only commit would be risky in this repo."""
    reasons: list[str] = []
    if _git(root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return ["not a git repo"]
    gdir_r = _git(root, "rev-parse", "--git-dir")
    gdir = Path(gdir_r.stdout.strip())
    if not gdir.is_absolute():
        gdir = root / gdir
    for marker in ("index.lock", "MERGE_HEAD", "rebase-merge", "rebase-apply", "CHERRY_PICK_HEAD"):
        if (gdir / marker).exists():
            reasons.append(f"git {marker} present")
    staged = _git(root, "diff", "--cached", "--name-only").stdout.split()
    if staged:
        reasons.append(f"index has staged changes ({len(staged)} path(s))")
    return reasons


def scan(targets: list[tuple[str, Path]], canonical_sha: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    harness_resolved = HARNESS_ROOT.resolve()
    for pid, root in targets:
        path = root / REL
        is_canon = root.resolve() == harness_resolved if root.exists() else False
        before = sha256(path)
        if not root.is_dir():
            status = "MISSING-REPO"
        elif is_canon:
            status = "CANONICAL"
        elif before is None:
            status = "MISSING-FILE"
        elif before == canonical_sha:
            status = "OK"
        else:
            status = "DRIFT"
        rows.append(
            {"id": pid, "root": root, "path": path, "before": before, "after": before, "status": status,
             "commit": "", "note": ""}
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="report drift; exit 1 on drift (default)")
    mode.add_argument("--write", action="store_true", help="copy canonical over drifted copies")
    ap.add_argument("--commit", action="store_true", help="with --write: commit only the lint file per repo")
    ap.add_argument("--products-file", type=Path, default=None)
    ap.add_argument("--root", action="append", default=[], type=Path, help="extra repo root (repeatable)")
    ap.add_argument("--skip", action="append", default=[], help="product id to leave untouched (STUCK)")
    ap.add_argument("--message", default=None, help="commit message (default: standard sync message)")
    args = ap.parse_args(argv)
    if args.commit and not args.write:
        ap.error("--commit requires --write")

    canonical_sha = sha256(CANONICAL)
    if canonical_sha is None:
        print(f"❌ canonical missing: {CANONICAL}")
        return 2
    targets = load_products(args.products_file)
    for extra in args.root:
        targets.append((extra.expanduser().name, extra.expanduser()))
    if not any(r.resolve() == HARNESS_ROOT.resolve() for _, r in targets if r.exists()):
        targets.insert(0, ("agent-harness", HARNESS_ROOT))
    rows = scan(targets, canonical_sha)
    skip = set(args.skip)

    if args.write:
        for row in rows:
            if row["status"] not in ("DRIFT", "MISSING-FILE"):
                continue
            if row["id"] in skip:
                row["status"] = "STUCK"
                row["note"] = "skipped (--skip: lock hold / parallel worker)"
                continue
            root: Path = row["root"]
            if args.commit:
                blockers = commit_blockers(root)
                if blockers:
                    row["status"] = "STUCK"
                    row["note"] = "; ".join(blockers)
                    continue
            row["path"].parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(CANONICAL, row["path"])
            row["after"] = sha256(row["path"])
            row["status"] = "SYNCED"
            if args.commit:
                rel = str(REL)
                msg = args.message or DEFAULT_MSG.format(sha=canonical_sha[:12] + "…")
                if row["before"] is None:
                    _git(root, "add", "--", rel)
                cr = _git(root, "commit", "--only", "-m", msg, "--", rel)
                if cr.returncode != 0:
                    row["status"] = "SYNCED-UNCOMMITTED"
                    row["note"] = (cr.stdout + cr.stderr).strip().splitlines()[-1:] or ["commit failed"]
                    row["note"] = str(row["note"][0])
                else:
                    row["commit"] = _git(root, "rev-parse", "--short", "HEAD").stdout.strip()

    print(f"canonical: {CANONICAL}")
    print(f"canonical sha256: {canonical_sha}")
    print("| repo | status | sha256 before | sha256 after | commit | note |")
    print("|------|--------|---------------|--------------|--------|------|")
    for row in rows:
        b = (row["before"] or "-")[:12]
        a = (row["after"] or "-")[:12]
        print(f"| {row['id']} ({row['root']}) | {row['status']} | {b} | {a} | {row['commit'] or '-'} | {row['note'] or ''} |")
    drift = [r for r in rows if r["status"] in ("DRIFT", "MISSING-FILE", "STUCK", "SYNCED-UNCOMMITTED")
             and r["after"] != canonical_sha]
    missing_repo = [r for r in rows if r["status"] == "MISSING-REPO"]
    in_sync = sum(1 for r in rows if (r["after"] or "") == canonical_sha)
    print(f"summary: {in_sync}/{len(rows)} byte-identical to canonical; drift={len(drift)}"
          + (f"; missing repos={len(missing_repo)}" if missing_repo else ""))
    if drift:
        print("❌ vault_schema_lint drift: " + ", ".join(r["id"] for r in drift))
        return 1
    print("✅ vault_schema_lint copies in sync with harness SoT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
