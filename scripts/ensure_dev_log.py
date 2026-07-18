#!/usr/bin/env python3
"""Seed or normalize vault ``dev-log.md`` headers to the Option A standard.

See docs/dev-log.md (agent-harness SoT).

Usage::

  python3 scripts/ensure_dev_log.py --vault /path/to/vault
  python3 scripts/ensure_dev_log.py --vault ... --label my-product
  python3 scripts/ensure_dev_log.py --vault ... --all-projects   # every 01-Projects/*/dev-log.md
  python3 scripts/ensure_dev_log.py --vault ... --dry-run
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _label_from_plugin(product_root: Path) -> str:
    plugin = product_root / ".agents" / "product_plugin.yaml"
    if not plugin.is_file():
        return "product"
    text = plugin.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^\s*project_label:\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip().strip("\"'")
    m = re.search(r"^\s*product_id:\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip().strip("\"'")
    return "product"


def standard_header(label: str) -> str:
    return (
        f"# {label} dev log\n\n"
        "Newest first. Times: UTC + HKT. Writers: harness `sync_vault_devlog` only.\n\n"
        f"Agent-appended development notes ({label} → optional knowledge vault).\n\n"
        "Two entry kinds (Option A — harness docs/dev-log.md):\n"
        "- **Release** (`/sync_docs`): `## YYYY-MM-DD — vX.Y.Z synced` + When/Kind/Release/…\n"
        "- **Note** (`--note`): `## YYYY-MM-DD — {title}` + When/Kind/Repo + bullets "
        "(never `synced` / bare semver title)\n\n"
    )


def split_header_and_rest(text: str) -> tuple[str, str]:
    if not text:
        return "", ""
    lines = text.splitlines(keepends=True)
    cut = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            cut = i
            break
    if cut is None:
        return text if text.endswith("\n") else text + "\n", ""
    return "".join(lines[:cut]), "".join(lines[cut:])


def ensure_file(path: Path, label: str, *, dry_run: bool) -> str:
    header = standard_header(label)
    if not path.is_file() or path.stat().st_size == 0:
        if dry_run:
            return f"would create {path} (label={label})"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(header, encoding="utf-8")
        return f"created {path}"

    existing = path.read_text(encoding="utf-8", errors="replace")
    old_header, rest = split_header_and_rest(existing)
    # Already standard?
    if (
        old_header.startswith(f"# {label} dev log")
        and "Newest first" in old_header
        and "sync_vault_devlog" in old_header
        and "Option A" in old_header
    ):
        return f"ok {path} (header already standard)"

    new_text = header + rest.lstrip("\n")
    if dry_run:
        return f"would normalize header {path} (label={label}, keep {rest.count('## ')} entries)"
    path.write_text(new_text, encoding="utf-8")
    return f"normalized {path}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="Vault root (or PRODUCT_VAULT_ROOT / WATCHLIST_VAULT_ROOT)",
    )
    ap.add_argument("--label", default=None, help="project_label (default: product plugin)")
    ap.add_argument(
        "--product-root",
        type=Path,
        default=ROOT,
        help="Product root for plugin label (default: this repo)",
    )
    ap.add_argument(
        "--all-projects",
        action="store_true",
        help="Normalize every 01-Projects/*/dev-log.md under vault",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    vault = args.vault
    if vault is None:
        env = os.environ.get("PRODUCT_VAULT_ROOT") or os.environ.get("WATCHLIST_VAULT_ROOT")
        vault = Path(env) if env else None
    if vault is None or not vault.is_dir():
        print(
            "⚠️  VAULT SKIP: set --vault or PRODUCT_VAULT_ROOT",
            file=sys.stderr,
        )
        return 0

    notes: list[str] = []
    if args.all_projects:
        projects = vault / "01-Projects"
        if not projects.is_dir():
            print(f"❌ no {projects}", file=sys.stderr)
            return 1
        for d in sorted(projects.iterdir()):
            if not d.is_dir() or d.name in ("harness-night-shift",):
                continue
            log = d / "dev-log.md"
            notes.append(ensure_file(log, d.name, dry_run=args.dry_run))
    else:
        label = args.label or _label_from_plugin(args.product_root)
        # honor plugin dev_log_rel when single product
        rel = f"01-Projects/{label}/dev-log.md"
        plugin = args.product_root / ".agents" / "product_plugin.yaml"
        if plugin.is_file():
            m = re.search(r"^\s*dev_log_rel:\s*(.+)$", plugin.read_text(), re.M)
            if m:
                rel = m.group(1).strip().strip("\"'")
        path = vault / rel
        notes.append(ensure_file(path, label, dry_run=args.dry_run))

    for n in notes:
        print(n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
