#!/usr/bin/env python3
"""Unified validation entry point. Wraps compliance_engine + hygiene + hardcodes.

FSM extra gate (full/hygiene): when a knowledge vault is present, run
``check_dev_log_contract`` for this product's ``01-Projects/<label>/dev-log.md``
(or all project logs if label unknown). Skipped when vault is absent/off.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent


def _run(cmd: list[str], label: str) -> int:
    print(f"\n── {label} ──")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"❌ {label} failed (exit {r.returncode})")
    else:
        print(f"✅ {label} passed")
    return r.returncode


def _project_label() -> str | None:
    try:
        sys.path.insert(0, str(SCRIPTS))
        from vault_resolve import load_vault_config  # type: ignore

        cfg = load_vault_config(ROOT)
        label = (cfg.get("project_label") or cfg.get("product_id") or "").strip()
        return label or None
    except Exception:
        pass
    plugin = ROOT / ".agents" / "product_plugin.yaml"
    if plugin.is_file():
        text = plugin.read_text(encoding="utf-8")
        for key in ("project_label", "product_id"):
            m = re.search(rf"^\s*{key}:\s*(.+)$", text, re.M)
            if m:
                return m.group(1).strip().strip("\"'")
    return ROOT.name if ROOT.name else None


def _resolve_vault() -> Path | None:
    """Return vault root if present and enabled; else None (gate skipped)."""
    try:
        sys.path.insert(0, str(SCRIPTS))
        from vault_resolve import resolve_vault_root  # type: ignore

        v = resolve_vault_root(cli_vault=None, product_root=ROOT, require_enabled=False)
        if v is not None:
            p = Path(v).expanduser().resolve()
            if p.is_dir() and (p / "01-Projects").is_dir():
                return p
    except Exception:
        pass
    for key in ("PRODUCT_VAULT_ROOT", "WATCHLIST_VAULT_ROOT", "SECOND_BRAIN_VAULT"):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        p = Path(raw).expanduser().resolve()
        if p.is_dir() and (p / "01-Projects").is_dir():
            return p
    default = Path("/opt/second-brain/vault")
    if default.is_dir() and (default / "01-Projects").is_dir():
        # Only use default if this product has a log there (or any projects exist)
        return default
    return None


def _dev_log_contract_gate() -> int:
    """Extra FSM gate: vault present → check_dev_log_contract (product-scoped)."""
    checker = SCRIPTS / "check_dev_log_contract.py"
    if not checker.is_file():
        print("\n── check_dev_log_contract ──")
        print("⏭️  skipped (check_dev_log_contract.py not installed)")
        return 0
    vault = _resolve_vault()
    if vault is None:
        print("\n── check_dev_log_contract ──")
        print("⏭️  skipped (vault not present / not configured)")
        return 0
    label = _project_label()
    cmd = [sys.executable, str(checker), "--vault", str(vault)]
    if label:
        log = vault / "01-Projects" / label / "dev-log.md"
        if not log.is_file():
            print("\n── check_dev_log_contract ──")
            print(f"⏭️  skipped (no {log.relative_to(vault)} yet — create via sync_vault_devlog)")
            return 0
        cmd += ["--project", label]
    print(f"\n── check_dev_log_contract (vault={vault}" + (f", project={label}" if label else "") + ") ──")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"❌ check_dev_log_contract failed (exit {r.returncode})")
    else:
        print("✅ check_dev_log_contract passed")
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["full", "hygiene", "compliance"])
    ap.add_argument("--diff", help="Git diff range, e.g. HEAD~1..HEAD")
    ap.add_argument("--scope", help="Module scope for compliance")
    ap.add_argument(
        "--skip-dev-log-contract",
        action="store_true",
        help="Skip vault dev-log contract gate even when vault is present",
    )
    args = ap.parse_args()
    py = sys.executable
    exits: list[int] = []

    if args.mode in ("full", "compliance"):
        cmd = [py, str(SCRIPTS / "compliance_engine.py")]
        if args.diff:
            cmd += ["--diff", args.diff]
        if args.scope:
            cmd += ["--scope", args.scope]
        exits.append(_run(cmd, "compliance_engine"))

    if args.mode in ("full", "hygiene"):
        exits.append(_run([py, str(SCRIPTS / "check_hardcodes.py")], "check_hardcodes"))
        exits.append(_run([py, str(SCRIPTS / "check_repo_hygiene.py")], "check_repo_hygiene"))
        exits.append(_run([py, str(SCRIPTS / "check_module_coverage.py")], "check_module_coverage"))
        if not args.skip_dev_log_contract:
            exits.append(_dev_log_contract_gate())

    failed = sum(1 for e in exits if e != 0)
    print(f"\n{'='*40}\n{len(exits)-failed}/{len(exits)} gates passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
