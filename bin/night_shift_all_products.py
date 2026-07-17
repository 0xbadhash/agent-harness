#!/usr/bin/env python3
"""Run night_shift readiness across all registered product repos (harness SoT).

Schedule: 03:15 Asia/Hong_Kong via agent-harness systemd timer.

Config (first found wins):
  1. $NIGHT_SHIFT_PRODUCTS_FILE
  2. <harness>/config/night_shift_products.yaml
  3. Built-in defaults under $HOME/*

Writes multi-product summary:
  - vault 01-Projects/harness-night-shift/SUMMARY.md (latest)
  - vault 01-Projects/harness-night-shift/log.md (append)
  - <harness>/.agents/artifacts/NIGHT_SHIFT_ALL_REPORT.md
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parent.parent
# Prefer env; fall back next to harness sibling dirs under $HOME (no /home/<user> literals).
_HOME = Path.home()
DEFAULT_VAULT = Path(os.environ.get("PRODUCT_VAULT_ROOT") or os.environ.get("WATCHLIST_VAULT_ROOT") or "/opt/second-brain/vault")
DEFAULT_PRODUCTS = [
    ("watchlist", _HOME / "watchlist"),
    ("email-detach", _HOME / "email-detach"),
    ("substack-push", _HOME / "substack-push"),
    ("second-brain", _HOME / "second-brain"),
    ("catalyxt", _HOME / "catalyxt.ltd"),
    ("agent-harness", HARNESS_ROOT),
    ("ocr-ledger", _HOME / "ocr-ledger"),
]


def _load_products(path: Path | None) -> list[tuple[str, Path]]:
    if path is None:
        env = os.environ.get("NIGHT_SHIFT_PRODUCTS_FILE")
        path = Path(env) if env else HARNESS_ROOT / "config" / "night_shift_products.yaml"
    if not path.is_file():
        return [(n, p) for n, p in DEFAULT_PRODUCTS if p.is_dir()]
    rows: list[tuple[str, Path]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # id: path  or  - id: path
        line = line.lstrip("-").strip()
        if ":" not in line:
            continue
        pid, proot = line.split(":", 1)
        pid = pid.strip()
        proot_p = Path(proot.strip().strip("\"'")).expanduser()
        if proot_p.is_dir():
            rows.append((pid, proot_p))
    return rows or [(n, p) for n, p in DEFAULT_PRODUCTS if p.is_dir()]


def run_one(
    name: str,
    root: Path,
    *,
    vault: Path,
    quick: bool,
    skip_live: bool,
    dry_run: bool,
) -> dict:
    script = root / "scripts" / "night_shift_readiness.py"
    # Prefer product copy; fall back to harness SoT with --root
    if script.is_file():
        cmd = [sys.executable, str(script), "--vault", str(vault)]
        cwd = root
    else:
        sot = HARNESS_ROOT / "scripts" / "night_shift_readiness.py"
        cmd = [sys.executable, str(sot), "--root", str(root), "--vault", str(vault)]
        cwd = root
    if quick:
        cmd.append("--quick")
    if skip_live:
        cmd.append("--skip-live")
    if dry_run:
        cmd.append("--dry-run")

    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=3600,
            env={
                **os.environ,
                "PRODUCT_VAULT_ROOT": str(vault),
                "WATCHLIST_VAULT_ROOT": str(vault),
            },
        )
        out = (r.stdout or "") + (r.stderr or "")
        return {
            "name": name,
            "root": str(root),
            "exit": r.returncode,
            "ok": r.returncode == 0,
            "tail": out[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "root": str(root),
            "exit": 124,
            "ok": False,
            "tail": "timeout 3600s",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "name": name,
            "root": str(root),
            "exit": 1,
            "ok": False,
            "tail": str(exc),
        }


def write_summary(vault: Path, when: datetime, rows: list[dict], dry_run: bool) -> list[str]:
    notes: list[str] = []
    passed = sum(1 for r in rows if r["ok"])
    total = len(rows)
    overall = "PASS" if passed == total else "FAIL"
    lines = [
        f"# Multi-product night shift — {when.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"**Overall:** {overall} ({passed}/{total} products)",
        "**Schedule:** 03:15 Asia/Hong_Kong (harness timer)",
        f"**SoT:** `{HARNESS_ROOT}`",
        "",
        "| Product | Result | Exit | Root |",
        "|---------|--------|------|------|",
    ]
    for r in rows:
        tag = "✅" if r["ok"] else "❌"
        lines.append(f"| {r['name']} | {tag} | {r['exit']} | `{r['root']}` |")
    lines.extend(["", "## Per-product failures (tails)", ""])
    fails = [r for r in rows if not r["ok"]]
    if not fails:
        lines.append("_All products green._")
    else:
        for r in fails:
            lines.append(f"### {r['name']}")
            lines.append("```")
            lines.append(r.get("tail") or "")
            lines.append("```")
            lines.append("")
    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "1. Open each product vault `01-Projects/<label>/TODO.md` for checkboxes.",
            "2. Fix failed products before `/execute_dev` on that repo.",
            "3. **Hard-stop:** no multi-repo auto-release from this job.",
            "",
        ]
    )
    body = "\n".join(lines)

    art = HARNESS_ROOT / ".agents" / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        (art / "NIGHT_SHIFT_ALL_REPORT.md").write_text(body, encoding="utf-8")
        notes.append(f"artifact: {art / 'NIGHT_SHIFT_ALL_REPORT.md'}")

    if dry_run:
        print(body)
        return notes

    if not vault.is_dir():
        notes.append(f"⚠️ VAULT SKIP: {vault}")
        return notes

    proj = vault / "01-Projects" / "harness-night-shift"
    try:
        proj.mkdir(parents=True, exist_ok=True)
        (proj / "SUMMARY.md").write_text(body, encoding="utf-8")
        notes.append(f"vault summary: {proj / 'SUMMARY.md'}")
        log = proj / "log.md"
        if not log.is_file():
            log.write_text(
                "# Multi-product night-shift log\n\nHarness SoT orchestrator.\n\n",
                encoding="utf-8",
            )
        with log.open("a", encoding="utf-8") as f:
            f.write("\n---\n\n")
            f.write(body)
        notes.append(f"vault log: {log}")
        # cross-product TODO
        todo_lines = [
            "# All products TODO (night_shift multi)",
            "",
            f"_Updated {when.strftime('%Y-%m-%d %H:%M UTC')} · **{overall}** ({passed}/{total})_",
            "",
            "## Products",
            "",
        ]
        for r in rows:
            box = "[x]" if r["ok"] else "[ ]"
            todo_lines.append(f"- {box} **{r['name']}** — see `01-Projects/{r['name']}/TODO.md`")
        todo_lines.extend(
            [
                "",
                "## Actions",
                "",
            ]
        )
        if fails:
            for r in fails:
                todo_lines.append(
                    f"- [ ] Fix readiness on **{r['name']}** (exit {r['exit']})"
                )
        else:
            todo_lines.append(
                "- [ ] All green — pick next product work from each roadmap Shaping section"
            )
        todo_lines.append("")
        (proj / "TODO.md").write_text("\n".join(todo_lines), encoding="utf-8")
        notes.append(f"vault TODO: {proj / 'TODO.md'}")
    except PermissionError as exc:
        notes.append(f"⚠️ VAULT SKIP: {exc}")
    return notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--vault",
        type=Path,
        default=Path(os.environ.get("PRODUCT_VAULT_ROOT") or os.environ.get("WATCHLIST_VAULT_ROOT") or str(DEFAULT_VAULT)),
    )
    ap.add_argument("--products-file", type=Path, default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--skip-live", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="Run only this product id (repeatable)",
    )
    args = ap.parse_args()

    products = _load_products(args.products_file)
    if args.only:
        allow = set(args.only)
        products = [(n, p) for n, p in products if n in allow]

    when = datetime.now(timezone.utc)
    print(f"night_shift_all: {len(products)} product(s) @ {when.isoformat()}")
    rows: list[dict] = []
    for name, root in products:
        print(f"--- {name} ({root}) ---")
        row = run_one(
            name,
            root,
            vault=args.vault.expanduser().resolve(),
            quick=args.quick,
            skip_live=args.skip_live,
            dry_run=args.dry_run,
        )
        rows.append(row)
        print(f"{'✅' if row['ok'] else '❌'} {name} exit={row['exit']}")

    for n in write_summary(args.vault.expanduser().resolve(), when, rows, args.dry_run):
        print(n)

    passed = sum(1 for r in rows if r["ok"])
    total = len(rows)
    overall = "PASS" if passed == total else "FAIL"
    print(f"{'✅' if overall == 'PASS' else '❌'} night_shift_all {overall} ({passed}/{total})")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
