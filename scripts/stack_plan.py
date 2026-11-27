#!/usr/bin/env python3
"""Plan a stacked ship from ticket blocking edges.

Tickets already declare ``**Blocked by:**`` edges. This planner reuses the ticket
DAG parser to produce:

- ordered layers (everything in a layer can be built in parallel),
- a review chunk per layer,
- a rough size estimate per layer.

Usage::

  python3 scripts/stack_plan.py --tickets .agents/specs/<slug>/tickets
  python3 scripts/stack_plan.py --tickets <dir> --write
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_ticket_dag import find_cycle, load_tickets  # noqa: E402

DEFAULT_ESTIMATE = 150
ESTIMATE_RE = re.compile(r"\*\*Estimate:\*\*\s*(\d+)", re.IGNORECASE)
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


class DependencyCycle(ValueError):
    """Raised when ticket blocking edges form a cycle."""

    def __init__(self, trail: list[str]) -> None:
        self.trail = trail
        super().__init__(" -> ".join(trail))


class MissingDependency(ValueError):
    """Raised when a ticket names a blocking edge that has no ticket file."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(", ".join(missing))


def _metadata(path: Path, default_estimate: int = DEFAULT_ESTIMATE) -> tuple[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = TITLE_RE.search(text)
    title = match.group(1).strip() if match else path.stem
    estimate = ESTIMATE_RE.search(text)
    return title, int(estimate.group(1)) if estimate else default_estimate


def build_plan(
    tickets_dir: Path, *, default_estimate: int = DEFAULT_ESTIMATE
) -> dict[str, Any]:
    """Return layers, chunks, titles, and estimates for a ticket directory.

    ``**Estimate:**`` wins per ticket; ``default_estimate`` is the documented
    fallback for tickets that do not size themselves.
    """
    tickets_dir = Path(tickets_dir)
    tickets = load_tickets(tickets_dir)
    cycle = find_cycle(tickets)
    if cycle:
        raise DependencyCycle(cycle)
    missing = sorted(
        {
            dep
            for info in tickets.values()
            for dep in cast(list[str], info["deps"])
            if dep not in tickets
        }
    )
    if missing:
        raise MissingDependency(missing)

    remaining = set(tickets)
    resolved: set[str] = set()
    layers: list[list[str]] = []
    while remaining:
        ready = sorted(
            tid
            for tid in remaining
            if all(
                dep in resolved or dep not in tickets
                for dep in cast(list[str], tickets[tid]["deps"])
            )
        )
        if not ready:
            raise DependencyCycle(sorted(remaining))
        layers.append(ready)
        resolved.update(ready)
        remaining.difference_update(ready)

    titles: dict[str, str] = {}
    estimates: dict[str, int] = {}
    for tid, info in tickets.items():
        title, estimate = _metadata(
            Path(cast(Path, info["path"])), default_estimate
        )
        titles[tid] = title
        estimates[tid] = estimate

    chunks = []
    for index, layer in enumerate(layers, 1):
        chunks.append(
            {
                "chunk": index,
                "tickets": layer,
                "titles": [titles[tid] for tid in layer],
                "est_loc": sum(estimates[tid] for tid in layer),
            }
        )

    return {
        "tickets_dir": str(tickets_dir),
        "layers": layers,
        "chunks": chunks,
        "titles": titles,
        "estimates": estimates,
        "total_est_loc": sum(estimates.values()),
    }


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Stack plan",
        "",
        f"**Tickets:** `{plan['tickets_dir']}`",
        f"**Layers:** {len(plan['layers'])} · "
        f"**Estimated LOC:** {plan['total_est_loc']}",
        "",
        "## Layers",
        "",
    ]
    titles = plan["titles"]
    estimates = plan["estimates"]
    for index, layer in enumerate(plan["layers"], 1):
        lines.append(f"### Layer {index}")
        lines.append("")
        lines.append("| Ticket | Title | Est. LOC |")
        lines.append("|--------|-------|----------|")
        for tid in layer:
            lines.append(f"| {tid} | {titles[tid]} | {estimates[tid]} |")
        lines.append("")
    lines.extend(["## Review chunks", ""])
    for chunk in plan["chunks"]:
        lines.append(
            f"### CHUNK {chunk['chunk']} — tickets {', '.join(chunk['tickets'])}"
        )
        lines.append("")
        lines.append(f"Estimated LOC: {chunk['est_loc']}")
        lines.append("")
        for title in chunk["titles"]:
            lines.append(f"- {title}")
        lines.append("")
    return "\n".join(lines)


def write_plan(root: Path, plan: dict[str, Any]) -> tuple[Path, Path]:
    out = Path(root) / ".agents" / "artifacts"
    out.mkdir(parents=True, exist_ok=True)
    markdown = out / "STACK_PLAN.md"
    data = out / "STACK_PLAN.json"
    markdown.write_text(render_markdown(plan), encoding="utf-8")
    data.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return markdown, data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickets", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--default-estimate",
        type=int,
        default=DEFAULT_ESTIMATE,
        help=f"LOC fallback for tickets without **Estimate:** (default {DEFAULT_ESTIMATE})",
    )
    args = ap.parse_args(argv)

    if not args.tickets.is_dir():
        print(f"❌ not a directory: {args.tickets}", file=sys.stderr)
        return 2
    try:
        plan = build_plan(args.tickets, default_estimate=args.default_estimate)
    except DependencyCycle as exc:
        print(f"❌ ticket dependency cycle: {exc}", file=sys.stderr)
        return 1
    except MissingDependency as exc:
        print(f"❌ ticket dependency has no ticket: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(plan, indent=2))
    else:
        print(render_markdown(plan))
    if args.write:
        markdown, data = write_plan(args.root, plan)
        print(f"✅ stack plan written: {markdown} · {data}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
