#!/usr/bin/env python3
"""P0 A5/A8 — bounded auto-remediate night FAILs + open ticket list.

For each FAIL product from morning triage / reports:
  1. Run night_shift_autofix.attempt_autofix on synthetic failed gates
  2. Re-run daytime_readiness_subset once
  3. Append remaining fails to NIGHT_FAIL_TICKETS.md (checkbox tickets)

  python3 scripts/night_fail_remediate.py
  python3 scripts/night_fail_remediate.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS / "scripts"))
DEFAULT_PRODUCTS = HARNESS / "config" / "night_shift_products.yaml"
OVERALL_RE = re.compile(r"Overall:\s*\**\s*(PASS|FAIL)\b", re.I)
FAIL_GATE = re.compile(r"^\|\s*`?([a-zA-Z0-9_]+)`?\s*\|\s*❌", re.M)


@dataclass
class RemediateResult:
    product_id: str
    root: Path
    before: str
    after: str
    attempts: list[str] = field(default_factory=list)
    open_tickets: list[str] = field(default_factory=list)


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


def _status(root: Path) -> tuple[str, list[str]]:
    for name in ("NIGHT_SHIFT_TODO.md", "NIGHT_SHIFT_REPORT.md"):
        p = root / ".agents" / "artifacts" / name
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        m = OVERALL_RE.search(text)
        overall = m.group(1).upper() if m else "UNKNOWN"
        gates = FAIL_GATE.findall(text)
        return overall, gates
    # morning triage table
    return "UNKNOWN", []


def _fail_products_from_triage() -> set[str]:
    mt = HARNESS / ".agents" / "artifacts" / "MORNING_TRIAGE.md"
    fails: set[str] = set()
    if not mt.is_file():
        return fails
    for line in mt.read_text(encoding="utf-8", errors="replace").splitlines():
        if "**FAIL**" in line or "| **FAIL**" in line:
            m = re.search(r"`([a-zA-Z0-9_-]+)`", line)
            if m:
                fails.add(m.group(1))
    return fails


def remediate_product(
    pid: str,
    root: Path,
    *,
    dry_run: bool,
) -> RemediateResult:
    before, gates = _status(root)
    attempts: list[str] = []
    if not root.is_dir():
        return RemediateResult(pid, root, before, "MISSING", open_tickets=["root missing"])

    # Build synthetic results for autofix
    results = [{"name": g or "validate_full", "ok": False, "tail": ""} for g in (gates or ["validate_full", "product_smoke"])]
    try:
        from night_shift_autofix import attempt_autofix  # type: ignore

        att = attempt_autofix(root, results, dry_run=dry_run, product_id=pid)
        for a in att:
            attempts.append(f"{a.get('name')}:{a.get('detail') or a.get('status')}")
    except Exception as exc:  # noqa: BLE001
        attempts.append(f"autofix_error:{exc}")

    # recheck daytime
    after = before
    if not dry_run:
        dr = HARNESS / "scripts" / "daytime_readiness_subset.py"
        if dr.is_file():
            r = subprocess.run(
                [sys.executable, str(dr), "--root", str(root)],
                cwd=str(HARNESS),
                check=False,
                capture_output=True,
                text=True,
            )
            after = "PASS" if r.returncode == 0 else "FAIL"
            attempts.append(f"daytime_recheck rc={r.returncode}")
        else:
            smoke = root / "scripts" / "product_smoke.py"
            if smoke.is_file():
                r2 = subprocess.run(
                    [sys.executable, str(smoke), "--root", str(root)],
                    cwd=str(root),
                    check=False,
                    capture_output=True,
                    text=True,
                )
                after = "PASS" if r2.returncode == 0 else "FAIL"

    tickets: list[str] = []
    if after != "PASS":
        for g in gates or ["unknown_gate"]:
            tickets.append(f"[{pid}] fix gate `{g}` until daytime_readiness / product_smoke green")
        if not tickets:
            tickets.append(f"[{pid}] readiness still FAIL after bounded autofix — investigate validate_full/product_smoke")
    return RemediateResult(pid, root, before, after, attempts=attempts, open_tickets=tickets)


def write_tickets(results: list[RemediateResult], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# NIGHT_FAIL_TICKETS",
        "",
        f"_Generated {now} by night_fail_remediate.py_",
        "",
        "Open after bounded autofix. Close when product readiness is green.",
        "",
    ]
    open_any = False
    for r in results:
        lines.append(f"## {r.product_id} ({r.before} → {r.after})")
        lines.append("")
        for a in r.attempts:
            lines.append(f"- attempt: {a}")
        if r.open_tickets:
            open_any = True
            for t in r.open_tickets:
                lines.append(f"- [ ] {t}")
        else:
            lines.append("- [x] cleared by bounded remediate")
        lines.append("")
    if not open_any:
        lines.append("_No open tickets._")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--products-file", type=Path, default=DEFAULT_PRODUCTS)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--out",
        type=Path,
        default=HARNESS / ".agents" / "artifacts" / "NIGHT_FAIL_TICKETS.md",
    )
    ap.add_argument("--all-fail-only", action="store_true", default=True)
    args = ap.parse_args(argv)

    products = _load_products(args.products_file.expanduser())
    triage_fails = _fail_products_from_triage()
    # also promote list
    results: list[RemediateResult] = []
    for pid, root in products:
        overall, _ = _status(root)
        if pid in triage_fails or overall == "FAIL":
            results.append(remediate_product(pid, root, dry_run=args.dry_run))
        elif not triage_fails and overall != "PASS":
            # unknown with no triage: skip unless explicitly fail
            continue

    if not results and triage_fails:
        # triage said fail but no matching product status — still try those ids
        by_id = {p: r for p, r in products}
        for pid in triage_fails:
            if pid in by_id:
                results.append(remediate_product(pid, by_id[pid], dry_run=args.dry_run))

    write_tickets(results, args.out)
    # also run promote
    prom = HARNESS / "scripts" / "promote_night_fails.py"
    if prom.is_file() and not args.dry_run:
        subprocess.run([sys.executable, str(prom)], cwd=str(HARNESS), check=False)

    still = [r for r in results if r.after != "PASS"]
    print(f"night_fail_remediate products={len(results)} still_fail={len(still)} out={args.out}")
    for r in results:
        print(f"  {r.product_id}: {r.before}→{r.after} tickets={len(r.open_tickets)}")
    return 1 if still else 0


if __name__ == "__main__":
    raise SystemExit(main())
