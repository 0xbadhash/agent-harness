#!/usr/bin/env python3
"""Validate ticket markdown DAGs (Blocked by edges, cycle detection, ready frontier)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import cast

BLOCKED_RE = re.compile(r"^\*\*Blocked by:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def _ticket_id(path: Path) -> str:
    m = re.match(r"^(\d+)", path.stem)
    return m.group(1) if m else path.stem


def load_tickets(directory: Path) -> dict[str, dict[str, object]]:
    tickets: dict[str, dict[str, object]] = {}
    for p in sorted(directory.glob("*.md")):
        tid = _ticket_id(p)
        text = p.read_text(encoding="utf-8", errors="replace")
        bm = BLOCKED_RE.search(text)
        deps: list[str] = []
        if bm:
            raw = bm.group(1).strip()
            if not raw.lower().startswith("none"):
                for tok in re.split(r"[,\s]+", raw):
                    tok = tok.strip().strip("#")
                    if tok and re.match(r"^[A-Za-z0-9_-]+$", tok):
                        deps.append(tok)
        sm = STATUS_RE.search(text)
        status = sm.group(1).strip().lower() if sm else "ready-for-agent"
        tickets[tid] = {"deps": deps, "status": status, "path": p}
    return tickets


def find_cycle(tickets: dict[str, dict[str, object]]) -> list[str] | None:
    state: dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=done

    def dfs(node: str, trail: list[str]) -> list[str] | None:
        state[node] = 1
        deps = cast(list[str], tickets.get(node, {}).get("deps", []))
        for dep in deps:
            if dep not in tickets:
                continue
            if state.get(dep, 0) == 1:
                return [*trail, dep]
            if state.get(dep, 0) == 0:
                res = dfs(dep, [*trail, dep])
                if res:
                    return res
        state[node] = 2
        return None

    for tid in sorted(tickets):
        if state.get(tid, 0) == 0:
            cyc = dfs(tid, [tid])
            if cyc:
                return cyc
    return None


def ready_frontier(tickets: dict[str, dict[str, object]]) -> list[str]:
    done = {
        tid for tid, info in tickets.items() if info["status"] in {"done", "closed", "completed"}
    }
    ready: list[str] = []
    for tid, info in sorted(tickets.items()):
        if tid in done:
            continue
        deps = cast(list[str], info["deps"])
        if all(d in done for d in deps):
            ready.append(tid)
    return ready


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("directory", type=Path, help="Directory of ticket *.md files")
    args = ap.parse_args(argv)
    if not args.directory.is_dir():
        print(f"❌ not a directory: {args.directory}", file=sys.stderr)
        return 2
    tickets = load_tickets(args.directory)
    cyc = find_cycle(tickets)
    if cyc:
        print(f"❌ ticket dependency cycle detected: {' -> '.join(cyc)}", file=sys.stderr)
        return 1
    frontier = ready_frontier(tickets)
    print(f"✅ ticket DAG valid ({len(tickets)} tickets); ready frontier: {', '.join(frontier) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
