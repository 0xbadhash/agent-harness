#!/usr/bin/env python3
"""Merge an approved PR stack in ticket order, stopping on the first failure.

Order comes from ``stack_plan.build_plan`` (dependency layers). PR numbers come
from a JSON map (``{"01": 56, "02": 62}``) or the same file under
``.agents/artifacts/PR_MAP.json``.

Default: merge one PR at a time and stop for the operator.
``--auto-merge``: ask GitHub to squash-merge once checks pass (opt-in).

Usage::

  python3 scripts/merge_stack.py --tickets .agents/specs/<slug>/tickets \
      --pr-map .agents/artifacts/PR_MAP.json --dry-run
  python3 scripts/merge_stack.py --tickets ... --pr-map ... --auto-merge
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from stack_plan import DependencyCycle, MissingDependency, build_plan  # noqa: E402

OK_CONCLUSIONS = {"SUCCESS", "SKIPPED", "NEUTRAL", None}


class StackMergeError(RuntimeError):
    """Raised when a PR in the stack cannot be merged in order."""


def ticket_order(plan: dict[str, Any]) -> list[str]:
    """Flatten the dependency layers into a merge order."""
    return [tid for layer in plan["layers"] for tid in layer]


def load_pr_map(path: Path | None, root: Path) -> dict[str, str]:
    """Return ticket id -> PR number. Missing file means an empty map."""
    candidate = path or (root / ".agents" / "artifacts" / "PR_MAP.json")
    if not candidate.is_file():
        return {}
    try:
        data = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StackMergeError(f"cannot read pr map {candidate}: {exc}") from exc
    if not isinstance(data, dict):
        raise StackMergeError(f"pr map {candidate} must be a JSON object")
    return {str(k): str(v) for k, v in data.items()}


def check_pr_state(payload: dict[str, Any]) -> tuple[bool, str]:
    """Return (ok, detail) for a ``gh pr view --json`` payload."""
    state = str(payload.get("state") or "").upper()
    if state != "OPEN":
        return False, f"state is {state or 'unknown'}"
    mergeable = str(payload.get("mergeable") or "").upper()
    if mergeable == "CONFLICTING":
        return False, "mergeable is CONFLICTING"
    failing = []
    for check in payload.get("statusCheckRollup") or []:
        conclusion = check.get("conclusion") or check.get("state")
        if str(conclusion).upper() not in OK_CONCLUSIONS:
            name = check.get("name") or check.get("context") or "check"
            failing.append(f"{name}={conclusion}")
    if failing:
        return False, "checks not green: " + ", ".join(failing)
    return True, "mergeable"


def merge(
    plan: dict[str, Any],
    pr_map: dict[str, str],
    *,
    gh: Callable[[list[str]], dict[str, Any]],
    dry_run: bool = False,
    auto_merge: bool = False,
) -> list[str]:
    """Merge in layer order. Raises StackMergeError on the first problem."""
    done: list[str] = []
    for tid in ticket_order(plan):
        pr = pr_map.get(tid) or pr_map.get(tid.lstrip("0"))
        if dry_run:
            done.append(f"would merge {tid} (PR {pr or '?'})")
            continue
        if not pr:
            raise StackMergeError(f"{tid}: no PR number in the pr map")
        payload = gh(["pr", "view", pr, "--json", "state,mergeable,statusCheckRollup"])
        ok, detail = check_pr_state(payload)
        if not ok:
            raise StackMergeError(f"{tid} (PR {pr}) is not mergeable: {detail}")
        argv = ["pr", "merge", pr, "--squash", "--delete-branch"]
        if auto_merge:
            argv.append("--auto")
        gh(argv)
        done.append(f"merged {tid} (PR {pr})")
    return done


def _gh(argv: list[str]) -> dict[str, Any]:
    run = subprocess.run(
        ["gh", *argv], capture_output=True, text=True, check=False
    )
    if run.returncode != 0:
        raise StackMergeError((run.stderr or "gh failed").strip()[:300])
    out = (run.stdout or "").strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except ValueError:
        return {}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickets", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-map", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--auto-merge", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    try:
        plan = build_plan(args.tickets)
        pr_map = load_pr_map(args.pr_map, args.root.resolve())
        done = merge(
            plan,
            pr_map,
            gh=_gh,
            dry_run=args.dry_run,
            auto_merge=args.auto_merge,
        )
    except (DependencyCycle, MissingDependency, StackMergeError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"merged": done}, indent=2))
    else:
        for line in done:
            print(f"✅ {line}")
        if not args.dry_run:
            print("NEXT: /release_mgmt once every PR is merged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
