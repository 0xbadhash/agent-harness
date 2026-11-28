#!/usr/bin/env python3
"""Run the unblocked ticket frontier in order, one fresh worktree per ticket.

Reuses the ticket DAG and the stack layers. Tickets in one layer run in
parallel up to ``--workers``. A failed ticket blocks its dependents.

A real run needs ``--command`` with ``{ticket}`` and ``{worktree}`` placeholders;
the command is the executor (for example a headless agent invocation). It is
split like a shell line into an argv list, so pipes and ``&&`` are not
supported; the executor script owns that logic. It may print ``SESSION=<id>``;
the id is recorded in ``.agents/artifacts/TICKET_RUNS.jsonl``.

Usage::

  python3 scripts/run_tickets.py --tickets .agents/specs/<slug>/tickets --dry-run
  python3 scripts/run_tickets.py --tickets ... --workers 2 \
      --command "agent run --cwd {worktree} --task {ticket}"
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_ticket_dag import load_tickets  # noqa: E402
from stack_plan import DependencyCycle, MissingDependency, build_plan  # noqa: E402

SESSION_RE = re.compile(r"SESSION=([A-Za-z0-9_.:-]+)")
SESSION_FIELD_RE = re.compile(r"^\*\*Session:\*\*.*$", re.MULTILINE)
STATUS_LINE_RE = re.compile(r"^\*\*Status:\*\*[^\n]*$", re.MULTILINE)


class TicketRunError(RuntimeError):
    """Raised when a ticket runner cannot start."""


@dataclass
class RunResult:
    ticket: str
    ok: bool
    session: str = ""
    detail: str = ""


Runner = Callable[[str, Path], str]


def _runs_path(root: Path) -> Path:
    return root / ".agents" / "artifacts" / "TICKET_RUNS.jsonl"


def record_runs(root: Path, results: list[RunResult]) -> None:
    """Append one JSON line per result."""
    path = _runs_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for result in results:
            row = asdict(result)
            row["ts"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            handle.write(json.dumps(row) + "\n")


def _ticket_file(directory: Path, tid: str) -> Path | None:
    for path in sorted(directory.glob("*.md")):
        match = re.match(r"^(\d+)", path.stem)
        stem_id = match.group(1) if match else path.stem
        if stem_id == tid:
            return path
    return None


def record_session(directory: Path, tid: str, session: str) -> None:
    """Write ``**Session:** <id>`` into the ticket file after a real run."""
    path = _ticket_file(Path(directory), tid)
    if path is None:
        return
    text = path.read_text(encoding="utf-8")
    line = f"**Session:** {session}"
    if SESSION_FIELD_RE.search(text):
        updated = SESSION_FIELD_RE.sub(line, text, count=1)
    else:
        match = STATUS_LINE_RE.search(text)
        if match:
            updated = text[: match.end()] + "\n" + line + text[match.end():]
        else:
            updated = text.rstrip() + "\n" + line + "\n"
    path.write_text(updated, encoding="utf-8")


def run_ticket_set(
    directory: Path,
    runner: Runner,
    *,
    workers: int = 2,
    dry_run: bool = False,
) -> list[RunResult]:
    """Run layers in order, stopping a branch when its dependency fails."""
    plan = build_plan(directory)
    tickets = load_tickets(directory)
    done: set[str] = set()
    failed: set[str] = set()
    results: list[RunResult] = []

    for layer in plan["layers"]:
        runnable: list[str] = []
        for tid in layer:
            deps = [dep for dep in tickets[tid]["deps"] if dep in tickets]
            if any(dep in failed for dep in deps) or not all(dep in done for dep in deps):
                results.append(
                    RunResult(tid, False, detail="blocked by an unfinished dependency")
                )
                failed.add(tid)
            else:
                runnable.append(tid)

        if dry_run:
            for tid in runnable:
                results.append(RunResult(tid, True, detail="would run"))
                done.add(tid)
            continue

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            futures = {
                tid: pool.submit(runner, tid, directory) for tid in runnable
            }
            for tid, future in futures.items():
                try:
                    session = future.result()
                except Exception as exc:  # noqa: BLE001
                    results.append(RunResult(tid, False, detail=str(exc)[:300]))
                    failed.add(tid)
                else:
                    results.append(RunResult(tid, True, session=session))
                    record_session(directory, tid, session)
                    done.add(tid)
    return results


def _worktree(root: Path, tid: str, base: str) -> Path:
    path = root / ".agents" / "worktrees" / tid
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        run = subprocess.run(
            ["git", "worktree", "add", "-b", f"ticket/{tid}", str(path), base],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if run.returncode != 0:
            raise TicketRunError((run.stderr or "git worktree add failed").strip()[:300])
    return path


def make_runner(root: Path, command: str, base: str) -> Runner:
    """Build the subprocess runner used by the CLI."""

    def runner(tid: str, _directory: Path) -> str:
        worktree = _worktree(root, tid, base)
        argv = command.replace("{ticket}", tid).replace("{worktree}", str(worktree))
        run = subprocess.run(
            shlex.split(argv), cwd=str(worktree), capture_output=True, text=True, check=False
        )
        if run.returncode != 0:
            raise TicketRunError((run.stderr or run.stdout or "executor failed").strip()[:300])
        match = SESSION_RE.search(run.stdout)
        return match.group(1) if match else f"local-{tid}"

    return runner


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickets", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--command", default="")
    ap.add_argument("--base", default="HEAD")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    if not args.dry_run and not args.command:
        print("❌ a real run needs --command with {ticket} and {worktree}", file=sys.stderr)
        return 2
    if args.dry_run and not Path(args.tickets).is_dir():
        print(f"❌ not a directory: {args.tickets}", file=sys.stderr)
        return 2

    runner = make_runner(root, args.command, args.base)
    try:
        results = run_ticket_set(
            args.tickets, runner, workers=args.workers, dry_run=args.dry_run
        )
    except (DependencyCycle, MissingDependency) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        record_runs(root, results)
    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            mark = "✅" if result.ok else "❌"
            tail = f" — {result.detail}" if result.detail else ""
            session = f" (session {result.session})" if result.session else ""
            print(f"{mark} {result.ticket}{session}{tail}")
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
