#!/usr/bin/env python3
"""A5/A8 — promote repeated night FAIL gates beyond TODO text.

Scans product NIGHT_SHIFT reports / MORNING_TRIAGE; counts FAIL gates;
writes .agents/artifacts/NIGHT_FAIL_PROMOTIONS.md.
Optional --write-stubs creates tests/night_fail_promotions/test_gate_<name>.py

  python3 scripts/promote_night_fails.py
  python3 scripts/promote_night_fails.py --min-count 2 --write-stubs
"""
from __future__ import annotations

import argparse
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS = HARNESS / "config" / "night_shift_products.yaml"
FAIL_GATE = re.compile(r"^\|\s*`?([a-zA-Z0-9_]+)`?\s*\|\s*❌", re.M)
OVERALL_FAIL = re.compile(r"Overall:\s*\**\s*FAIL\b", re.I)
UNCHECKED_GATE = re.compile(r"^\s*-\s*\[\s*\]\s*`([a-zA-Z0-9_]+)`", re.M)


@dataclass
class Promotion:
    gate: str
    count: int
    products: list[str] = field(default_factory=list)
    action: str = ""


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


def _scan_root(pid: str, root: Path) -> list[str]:
    gates: list[str] = []
    for name in ("NIGHT_SHIFT_REPORT.md", "NIGHT_SHIFT_TODO.md", "MORNING_TRIAGE.md"):
        p = root / ".agents" / "artifacts" / name
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        gates.extend(FAIL_GATE.findall(text))
    return gates


def evaluate(
    products: list[tuple[str, Path]],
    *,
    min_count: int = 2,
) -> list[Promotion]:
    per_gate_products: dict[str, set[str]] = {}
    counts: Counter[str] = Counter()
    for pid, root in products:
        if not root.is_dir():
            continue
        for g in _scan_root(pid, root):
            counts[g] += 1
            per_gate_products.setdefault(g, set()).add(pid)

    # Also scan harness MORNING_TRIAGE table product FAIL lines
    mt = HARNESS / ".agents" / "artifacts" / "MORNING_TRIAGE.md"
    if mt.is_file():
        for line in mt.read_text(encoding="utf-8", errors="replace").splitlines():
            if "**FAIL**" in line or "| **FAIL**" in line:
                # product id in backticks
                m = re.search(r"`([a-zA-Z0-9_-]+)`", line)
                if m:
                    counts["product_fail"] += 1
                    per_gate_products.setdefault("product_fail", set()).add(m.group(1))

    promos: list[Promotion] = []
    for gate, n in counts.most_common():
        prods = sorted(per_gate_products.get(gate, []))
        # promote if count >= min or appears in >= min products
        if n < min_count and len(prods) < min_count:
            continue
        action = (
            f"Add/extend smoke or unit covering gate `{gate}`; "
            f"or fix root cause in products: {', '.join(prods) or 'n/a'}"
        )
        if gate == "product_fail":
            action = "Run morning_triage --recheck; open NIGHT_SHIFT_TODO for FAIL products"
        promos.append(Promotion(gate=gate, count=n, products=prods, action=action))
    return promos


def write_artifact(promos: list[Promotion], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# NIGHT_FAIL_PROMOTIONS",
        "",
        f"_Generated {now} by promote_night_fails.py_",
        "",
        "Repeated night FAIL gates promoted above one-off TODOs.",
        "",
        "| Gate | Count | Products | Suggested action |",
        "|------|-------|----------|------------------|",
    ]
    if not promos:
        lines.append("| — | 0 | — | No repeated fails at threshold |")
    for p in promos:
        lines.append(
            f"| `{p.gate}` | {p.count} | {', '.join(p.products) or '—'} | {p.action} |"
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- Fix root causes, then re-run night_shift / morning_triage.",
            "- Optional: `promote_night_fails.py --write-stubs` for placeholder tests.",
            "- This does **not** auto-ship product fixes.",
            "",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


_STUB = '''"""Promoted night-fail gate: {gate} — fill with real assertion."""
from __future__ import annotations

import unittest


class TestNightFail_{safe}(unittest.TestCase):
    def test_gate_documented(self):
        # Placeholder: replace with real smoke/unit for gate `{gate}`
        self.assertTrue(True, "stub — implement coverage for night fail gate {gate}")


if __name__ == "__main__":
    unittest.main()
'''


def write_stubs(promos: list[Promotion], tests_dir: Path) -> list[Path]:
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    written: list[Path] = []
    for p in promos:
        if p.gate == "product_fail":
            continue
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", p.gate)
        path = tests_dir / f"test_gate_{safe}.py"
        if path.is_file():
            continue
        path.write_text(_STUB.format(gate=p.gate, safe=safe), encoding="utf-8")
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--products-file", type=Path, default=DEFAULT_PRODUCTS)
    ap.add_argument("--min-count", type=int, default=2)
    ap.add_argument("--write-stubs", action="store_true")
    ap.add_argument(
        "--out",
        type=Path,
        default=HARNESS / ".agents" / "artifacts" / "NIGHT_FAIL_PROMOTIONS.md",
    )
    args = ap.parse_args(argv)
    products = _load_products(args.products_file.expanduser())
    # always include harness
    if not any(p[0] == "agent-harness" for p in products):
        products.append(("agent-harness", HARNESS))
    promos = evaluate(products, min_count=args.min_count)
    write_artifact(promos, args.out)
    print(f"promote_night_fails n={len(promos)} out={args.out}")
    for p in promos:
        print(f"  {p.gate}: count={p.count} products={p.products}")
    if args.write_stubs and promos:
        written = write_stubs(promos, HARNESS / "tests" / "night_fail_promotions")
        for w in written:
            print(f"  stub {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
