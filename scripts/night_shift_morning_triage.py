#!/usr/bin/env python3
"""Morning triage after night_shift — aggregate FAIL/TODO; optional recheck.

Does **not** auto-ship or invent features. Exit 1 if any product remains FAIL.

  python3 scripts/night_shift_morning_triage.py
  python3 scripts/night_shift_morning_triage.py --recheck
  python3 scripts/night_shift_morning_triage.py --products-file config/night_shift_products.yaml
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
DEFAULT_PRODUCTS = HARNESS / "config" / "night_shift_products.yaml"
# Matches both `**Overall:** **PASS**` and prose `Overall: **PASS**.`
OVERALL_RE = re.compile(
    r"\**Overall:\**\s*\**\s*(PASS|FAIL)\b",
    re.I,
)
FAIL_GATE = re.compile(
    r"^\s*-\s*\[\s*\]\s*`([a-zA-Z0-9_]+)`|"  # unchecked gate checkbox
    r"^\|\s*`?([a-zA-Z0-9_]+)`?\s*\|\s*❌",
    re.M,
)

@dataclass
class ProductResult:
    product_id: str
    root: Path
    overall: str  # PASS | FAIL | UNKNOWN | MISSING
    fail_gates: list[str] = field(default_factory=list)
    rechecked: bool = False
    recheck_ok: bool | None = None
    notes: str = ""


def _load_products(path: Path) -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        pid, raw = line.split(":", 1)
        root = Path(os.path.expanduser(raw.strip())).resolve()
        out.append((pid.strip(), root))
    return out


def _read_overall(root: Path) -> tuple[str, list[str]]:
    report = root / ".agents" / "artifacts" / "NIGHT_SHIFT_REPORT.md"
    todo = root / ".agents" / "artifacts" / "NIGHT_SHIFT_TODO.md"
    text = ""
    for p in (todo, report):
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            break
    if not text:
        return "MISSING", []
    m = OVERALL_RE.search(text)
    overall = m.group(1).upper() if m else "UNKNOWN"
    gates: list[str] = []
    for g in FAIL_GATE.findall(text):
        # findall returns tuples when multiple groups
        if isinstance(g, tuple):
            gates.append(next(x for x in g if x))
        else:
            gates.append(g)
    # Only treat explicit ❌ table fails as override; unchecked optional recs are not FAIL
    table_fails = re.findall(r"^\|\s*`?([a-zA-Z0-9_]+)`?\s*\|\s*❌", text, re.M)
    if overall == "PASS" and table_fails:
        overall = "FAIL"
        gates = table_fails
    elif table_fails:
        gates = table_fails
    return overall, gates

def _recheck(root: Path) -> bool:
    """Run daytime readiness subset for one product; True if exit 0."""
    script = HARNESS / "scripts" / "daytime_readiness_subset.py"
    if not script.is_file():
        # product-local smoke
        smoke = root / "scripts" / "product_smoke.py"
        if smoke.is_file():
            r = subprocess.run(
                [sys.executable, str(smoke), "--root", str(root)],
                cwd=str(root),
                check=False,
            )
            return r.returncode == 0
        return False
    r = subprocess.run(
        [sys.executable, str(script), "--root", str(root)],
        cwd=str(HARNESS),
        check=False,
    )
    return r.returncode == 0


def evaluate(
    products: list[tuple[str, Path]],
    *,
    recheck: bool = False,
) -> list[ProductResult]:
    results: list[ProductResult] = []
    for pid, root in products:
        if not root.is_dir():
            results.append(
                ProductResult(pid, root, "MISSING", notes="root missing")
            )
            continue
        overall, gates = _read_overall(root)
        pr = ProductResult(pid, root, overall, fail_gates=gates)
        if recheck and overall in ("FAIL", "UNKNOWN", "MISSING"):
            pr.rechecked = True
            ok = _recheck(root)
            pr.recheck_ok = ok
            if ok:
                pr.overall = "PASS"
                pr.notes = "recheck green"
            else:
                pr.overall = "FAIL"
                pr.notes = "recheck still red"
        results.append(pr)
    return results


def write_artifact(results: list[ProductResult], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    any_fail = any(r.overall != "PASS" for r in results)
    lines = [
        "# MORNING_TRIAGE",
        "",
        f"_Generated {now} by night_shift_morning_triage.py_",
        "",
        f"**Overall:** {'FAIL' if any_fail else 'PASS'}",
        "",
        "| Product | Path | Night overall | Fail gates | Recheck | Notes |",
        "|---------|------|---------------|------------|---------|-------|",
    ]
    for r in results:
        gates = ", ".join(r.fail_gates) if r.fail_gates else "—"
        rc = (
            "yes→ok"
            if r.rechecked and r.recheck_ok
            else "yes→fail"
            if r.rechecked and r.recheck_ok is False
            else "no"
        )
        lines.append(
            f"| `{r.product_id}` | `{r.root}` | **{r.overall}** | {gates} | {rc} | {r.notes or '—'} |"
        )
    lines.extend(
        [
            "",
            "## Operator next",
            "",
            "- If **PASS**: safe to start product work.",
            "- If **FAIL**: open product `.agents/artifacts/NIGHT_SHIFT_TODO.md` or vault TODO; fix gates then re-run readiness.",
            "- This tool does **not** auto-ship. Unattended `/execute_dev` is out of scope.",
            "",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--products-file",
        type=Path,
        default=Path(os.environ.get("NIGHT_SHIFT_PRODUCTS_FILE", DEFAULT_PRODUCTS)),
    )
    ap.add_argument("--recheck", action="store_true", help="Re-run daytime readiness once for non-PASS")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Default: harness .agents/artifacts/MORNING_TRIAGE.md",
    )
    ap.add_argument(
        "--root",
        type=Path,
        action="append",
        default=[],
        help="Single product root (repeatable); overrides products file when set",
    )
    args = ap.parse_args(argv)

    if args.root:
        products = [(p.name, p.resolve()) for p in args.root]
    else:
        products = _load_products(args.products_file.expanduser())
    if not products:
        print("night_shift_morning_triage: no products", file=sys.stderr)
        return 2

    results = evaluate(products, recheck=args.recheck)
    out = args.out or (HARNESS / ".agents" / "artifacts" / "MORNING_TRIAGE.md")
    write_artifact(results, out)
    any_fail = any(r.overall != "PASS" for r in results)
    print(f"morning_triage overall={'FAIL' if any_fail else 'PASS'} out={out}")
    for r in results:
        print(f"  {r.product_id}: {r.overall}" + (f" ({r.notes})" if r.notes else ""))
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
