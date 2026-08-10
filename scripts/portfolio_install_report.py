#!/usr/bin/env python3
"""A4 — after harness release: portfolio version residual report (+ optional install).

  python3 scripts/portfolio_install_report.py
  python3 scripts/portfolio_install_report.py --install
  python3 scripts/portfolio_install_report.py --install --force   # reinstall even if version matches
  python3 scripts/portfolio_install_report.py --install --push   # opt-in git push per product
  python3 scripts/portfolio_install_report.py --protect-drift    # checksum protect-list vs SoT

Default is report-only. Never force-push.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS = HARNESS / "config" / "night_shift_products.yaml"
INSTALL = HARNESS / "install_into_product.sh"
DEFAULT_PROTECT = HARNESS / "config" / "default_protect_scripts.txt"


@dataclass
class ProductRow:
    product_id: str
    root: Path
    harness_version: str | None
    sot_version: str
    lagging: bool
    notes: str = ""
    protect_drift: list[str] = field(default_factory=list)


def _load_products(path: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        pid, raw = line.split(":", 1)
        out.append((pid.strip(), Path(os.path.expanduser(raw.strip())).resolve()))
    return out


def _sot_version() -> str:
    p = HARNESS / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.is_file() else "unknown"


def evaluate(products: list[tuple[str, Path]], sot: str) -> list[ProductRow]:
    rows: list[ProductRow] = []
    for pid, root in products:
        if pid == "agent-harness":
            continue  # SoT itself
        if not root.is_dir():
            rows.append(ProductRow(pid, root, None, sot, True, "root missing"))
            continue
        hv = root / ".agents" / "HARNESS_VERSION"
        ver = None
        if hv.is_file():
            ver = hv.read_text(encoding="utf-8").lstrip("\ufeff").strip()
        lag = ver != sot
        notes = "" if not lag else f"product {ver!r} != SoT {sot!r}"
        rows.append(ProductRow(pid, root, ver, sot, lag, notes))
    return rows


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def _load_protect_relpaths() -> list[str]:
    paths: list[str] = []
    if not DEFAULT_PROTECT.is_file():
        return paths
    for line in DEFAULT_PROTECT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # normalize scripts/foo.py
        if not line.startswith("scripts/") and line.endswith(".py"):
            line = f"scripts/{line}" if "/" not in line else line
        paths.append(line)
    return paths


def protect_drift_for(root: Path) -> list[str]:
    """Return list of protect-list paths that differ from harness SoT (or missing)."""
    drifted: list[str] = []
    for rel in _load_protect_relpaths():
        sot = HARNESS / rel
        prod = root / rel
        if not sot.is_file():
            continue
        hs = _sha256(sot)
        ps = _sha256(prod)
        if ps is None:
            drifted.append(f"{rel}:missing_in_product")
        elif hs != ps:
            drifted.append(f"{rel}:diverged")
    return drifted


def write_report(rows: list[ProductRow], sot: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lag_n = sum(1 for r in rows if r.lagging)
    drift_n = sum(1 for r in rows if r.protect_drift)
    lines = [
        "# PORTFOLIO_INSTALL_REPORT",
        "",
        f"_Generated {now} · harness SoT VERSION=`{sot}`_",
        "",
        f"**Lagging products:** {lag_n} / {len(rows)}",
        f"**Protect-list drift:** {drift_n} / {len(rows)} (warn only; install does not overwrite protect forks)",
        "",
        "| Product | Path | HARNESS_VERSION | Lagging | Protect drift | Notes |",
        "|---------|------|-----------------|---------|---------------|-------|",
    ]
    for r in rows:
        drift = ", ".join(r.protect_drift[:4]) if r.protect_drift else "—"
        if len(r.protect_drift) > 4:
            drift += f" (+{len(r.protect_drift) - 4})"
        lines.append(
            f"| `{r.product_id}` | `{r.root}` | `{r.harness_version}` | "
            f"{'YES' if r.lagging else 'no'} | {drift} | {r.notes or '—'} |"
        )
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "```bash",
            "python3 scripts/portfolio_install_report.py",
            "python3 scripts/portfolio_install_report.py --protect-drift",
            "python3 scripts/portfolio_install_report.py --install",
            "python3 scripts/portfolio_install_report.py --install --force",
            "python3 scripts/portfolio_install_report.py --install --push",
            "```",
            "",
            "Default report-only. `--force` reinstalls even when VERSION matches.",
            "`--push` only after successful install commit. Protect-list files are never overwritten by install.",
            "",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _install(root: Path) -> int:
    if not INSTALL.is_file():
        return 2
    r = subprocess.run(
        ["bash", str(INSTALL), str(root), "--delete-stale-skills"],
        cwd=str(HARNESS),
        check=False,
    )
    return int(r.returncode)


def _git_commit_push(root: Path, *, push: bool) -> str:
    subprocess.run(["git", "add", "-A", "--", "scripts/", ".agents/", "tools/"], cwd=str(root), check=False)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "chore(harness): reinstall from portfolio_install_report",
        ],
        cwd=str(root),
        check=False,
        capture_output=True,
    )
    if push:
        r = subprocess.run(
            ["git", "push", "origin", "HEAD"],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
        )
        return f"push rc={r.returncode}"
    return "committed or clean (no push)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--products-file", type=Path, default=DEFAULT_PRODUCTS)
    ap.add_argument("--install", action="store_true")
    ap.add_argument(
        "--force",
        action="store_true",
        help="With --install: reinstall even when HARNESS_VERSION matches SoT",
    )
    ap.add_argument(
        "--protect-drift",
        action="store_true",
        help="Compare protect-list scripts to harness SoT (warn; never overwrite)",
    )
    ap.add_argument("--push", action="store_true", help="With --install: git push after commit")
    ap.add_argument(
        "--out",
        type=Path,
        default=HARNESS / ".agents" / "artifacts" / "PORTFOLIO_INSTALL_REPORT.md",
    )
    args = ap.parse_args(argv)
    if args.push and not args.install:
        print("--push requires --install", file=sys.stderr)
        return 2
    if args.force and not args.install:
        print("--force requires --install", file=sys.stderr)
        return 2
    sot = _sot_version()
    products = _load_products(args.products_file.expanduser())
    rows = evaluate(products, sot)
    if args.protect_drift or args.install:
        for r in rows:
            if r.root.is_dir():
                r.protect_drift = protect_drift_for(r.root)
    if args.install:
        for r in rows:
            if not r.root.is_dir():
                r.notes = "skip install: missing root"
                continue
            if not r.lagging and not args.force and r.notes != "root missing":
                if r.protect_drift:
                    r.notes = f"skip install (version match); protect_drift={len(r.protect_drift)}"
                continue
            rc = _install(r.root)
            note = _git_commit_push(r.root, push=args.push)
            force_s = " force" if args.force else ""
            r.notes = f"install{force_s} rc={rc}; {note}"
            # refresh version
            hv = r.root / ".agents" / "HARNESS_VERSION"
            r.harness_version = hv.read_text(encoding="utf-8").strip() if hv.is_file() else r.harness_version
            r.lagging = r.harness_version != sot
            if args.protect_drift:
                r.protect_drift = protect_drift_for(r.root)
    write_report(rows, sot, args.out)
    lag = sum(1 for r in rows if r.lagging)
    drift = sum(1 for r in rows if r.protect_drift)
    print(f"portfolio_install sot={sot} lagging={lag} protect_drift={drift} out={args.out}")
    for r in rows:
        extra = f" drift={len(r.protect_drift)}" if r.protect_drift else ""
        print(f"  {r.product_id}: ver={r.harness_version} lag={r.lagging}{extra} {r.notes}")
    return 1 if lag else 0


if __name__ == "__main__":
    raise SystemExit(main())
