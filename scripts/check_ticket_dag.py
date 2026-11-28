#!/usr/bin/env python3
"""Validate ticket markdown DAGs (Blocked by edges, cycle detection, ready frontier)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, cast

BLOCKED_RE = re.compile(r"^\*\*Blocked by:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)
KIND_RE = re.compile(r"^\*\*Kind:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)
PREFACTOR_RE = re.compile(
    r"^\*\*Prefactor:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE
)
TOUCHES_RE = re.compile(r"^\*\*Touches:\*\*\s*(.+)$", re.IGNORECASE | re.MULTILINE)
DASH_NOTE_RE = re.compile(r"\s+(?:—|–|-{1,2})\s+.*$")
NONE_VALUES = {"none", "n/a", "na", "-", "none."}


def _ids(raw: str) -> list[str]:
    """Split a dependency field into ticket-id tokens.

    The template's ``None — can start immediately`` means no dependency; strip
    the trailing note before checking for the none value.
    """
    text = DASH_NOTE_RE.sub("", raw.strip())
    if text.strip().lower() in NONE_VALUES:
        return []
    out: list[str] = []
    for token in re.split(r"[,\s]+", text.strip()):
        token = token.strip().strip("#`[]().")
        if token and re.match(r"^[A-Za-z0-9_-]+$", token):
            out.append(token)
    return out


def _short(ticket_id: str) -> str:
    match = re.match(r"^(\d+)", ticket_id)
    return match.group(1) if match else ticket_id


def _ticket_id(path: Path) -> str:
    m = re.match(r"^(\d+)", path.stem)
    return m.group(1) if m else path.stem


def _touches(raw: str) -> list[str]:
    """Split a Touches field into repo-relative path tokens."""
    text = DASH_NOTE_RE.sub("", raw.strip())
    if text.strip().lower() in NONE_VALUES:
        return []
    return [
        token.strip("`[]().")
        for token in re.split(r"[,\s]+", text)
        if token.strip("`[]().")
    ]


def load_tickets(directory: Path) -> dict[str, dict[str, Any]]:
    tickets: dict[str, dict[str, Any]] = {}
    for p in sorted(directory.glob("*.md")):
        tid = _ticket_id(p)
        text = p.read_text(encoding="utf-8", errors="replace")
        bm = BLOCKED_RE.search(text)
        deps: list[str] = _ids(bm.group(1)) if bm else []
        # A prefactor ticket is a blocking edge: it must land first.
        pm = PREFACTOR_RE.search(text)
        prefactor = _ids(pm.group(1)) if pm else []
        deps.extend(p for p in prefactor if p not in deps)
        km = KIND_RE.search(text)
        kind = km.group(1).strip().lower() if km else ""
        tm = TOUCHES_RE.search(text)
        touches = _touches(tm.group(1)) if tm else []
        sm = STATUS_RE.search(text)
        status = sm.group(1).strip().lower() if sm else "ready-for-agent"
        tickets[tid] = {
            "deps": deps,
            "status": status,
            "path": p,
            "kind": kind,
            "prefactor": prefactor,
            "touches": touches,
        }
    return tickets


def validate_prefactors(tickets: dict[str, dict[str, object]]) -> list[str]:
    """E25 — a shared-component ticket names a prefactor that exists."""
    by_short = {_short(tid): tid for tid in tickets}
    failures: list[str] = []
    for tid, info in sorted(tickets.items()):
        kind = str(info.get("kind") or "")
        prefactor = cast(list[str], info.get("prefactor") or [])
        if kind == "shared-component" and not prefactor:
            failures.append(
                f"{tid}: **Kind:** shared-component needs a **Prefactor:** ticket"
            )
        for ref in prefactor:
            if ref not in tickets and _short(ref) not in by_short:
                failures.append(f"{tid}: prefactor {ref!r} has no ticket file")
    return failures


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
    prefactor_failures = validate_prefactors(tickets)
    if prefactor_failures:
        for failure in prefactor_failures:
            print(f"❌ {failure}", file=sys.stderr)
        return 1
    frontier = ready_frontier(tickets)
    print(f"✅ ticket DAG valid ({len(tickets)} tickets); ready frontier: {', '.join(frontier) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
