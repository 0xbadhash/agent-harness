#!/usr/bin/env python3
"""Fork-sync bot: turn local/origin divergence into a tracker issue (E25).

The harness can drift from ``origin/main`` for days because nothing pages on
it. This bot compares the two refs and, when they diverge, prepares a tracker
issue with the exact ahead/behind counts and repair steps.

Dry-run is the default: it prints the issue draft and touches nothing. Passing
``--create`` is the only path that runs ``gh issue create`` (network). Run
``git fetch`` yourself first; this script does not fetch.

Usage::

  python3 scripts/fork_sync_bot.py --root .
  python3 scripts/fork_sync_bot.py --root . --create --repo owner/name
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LABEL = "fork-drift"


@dataclass(frozen=True)
class Divergence:
    ahead: int
    behind: int

    @property
    def diverged(self) -> bool:
        return bool(self.ahead or self.behind)


Runner = Callable[[list[str], Path], "subprocess.CompletedProcess[str]"]


def default_runner(cmd: list[str], cwd: Path) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def parse_counts(text: str) -> Divergence:
    """Parse ``git rev-list --left-right --count A...B`` (ahead, behind)."""
    parts = text.split()
    if len(parts) != 2:
        raise ValueError(f"expected two counts, got {text!r}")
    ahead, behind = (int(part) for part in parts)
    return Divergence(ahead=ahead, behind=behind)


def git_divergence(
    root: Path = ROOT,
    *,
    remote: str = "origin",
    branch: str = "main",
    runner: Runner | None = None,
) -> Divergence:
    """Return local-vs-remote divergence for ``branch`` without fetching."""
    run = runner or default_runner
    ref = f"{remote}/{branch}"
    result = run(["git", "rev-list", "--left-right", "--count", f"{ref}...{branch}"], Path(root))
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"cannot compare {ref} to {branch}: {detail}")
    return parse_counts(result.stdout)


def issue_title(divergence: Divergence, *, remote: str = "origin", branch: str = "main") -> str:
    return (
        f"fork drift: local {branch} is {divergence.ahead} ahead / "
        f"{divergence.behind} behind {remote}/{branch}"
    )


def issue_body(
    divergence: Divergence,
    *,
    remote: str = "origin",
    branch: str = "main",
    when: datetime | None = None,
) -> str:
    when = when or datetime.now(UTC)
    direction = []
    if divergence.ahead:
        direction.append(f"{divergence.ahead} local commit(s) not pushed")
    if divergence.behind:
        direction.append(f"{divergence.behind} upstream commit(s) not pulled")
    lines = [
        f"Local `{branch}` has diverged from `{remote}/{branch}`.",
        "",
        f"- ahead: {divergence.ahead}",
        f"- behind: {divergence.behind}",
        "",
        "This tracker issue exists so the drift cannot stay silent.",
        "",
        "## Evidence",
        "",
        "```",
        f"git rev-list --left-right --count {remote}/{branch}...{branch}",
        f"{divergence.ahead}\t{divergence.behind}",
        "```",
        "",
        "## Repair",
        "",
        "1. `git fetch " + remote + "` to confirm these counts are current.",
        f"2. Inspect each {branch} commit before replaying it: `git log --oneline {remote}/{branch}..{branch}`.",
        "3. Rebase or merge deliberately; never force-push shared history.",
        "4. Re-run the daytime gates and close this issue with the green run link.",
        "",
        f"_Detected {when:%Y-%m-%dT%H:%M:%SZ} by `scripts/fork_sync_bot.py`._",
    ]
    if direction:
        lines.insert(4, "- " + "; ".join(direction))
    return "\n".join(lines)


def open_issue(
    title: str,
    body: str,
    *,
    repo: str = "",
    label: str = DEFAULT_LABEL,
    root: Path = ROOT,
    runner: Runner | None = None,
) -> "subprocess.CompletedProcess[str]":
    """Create the tracker issue with ``gh``. Network only on this path."""
    run = runner or default_runner
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    if repo:
        cmd.extend(["--repo", repo])
    if label:
        cmd.extend(["--label", label])
    result = run(cmd, Path(root))
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"gh issue create failed: {detail}")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--repo", default="", help="GitHub owner/name (gh default when omitted)")
    ap.add_argument("--label", default=DEFAULT_LABEL)
    ap.add_argument("--create", action="store_true", help="actually open the issue")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    try:
        divergence = git_divergence(root, remote=args.remote, branch=args.branch)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "ahead": divergence.ahead,
                    "behind": divergence.behind,
                    "diverged": divergence.diverged,
                }
            )
        )
    if not divergence.diverged:
        print(f"✅ no drift: local {args.branch} matches {args.remote}/{args.branch}")
        return 0

    title = issue_title(divergence, remote=args.remote, branch=args.branch)
    body = issue_body(divergence, remote=args.remote, branch=args.branch)
    if not args.create:
        print(f"⚠️  {title}")
        print("(dry run — issue draft below; pass --create to file it)")
        print()
        print(f"title: {title}")
        print()
        print(body)
        return 0

    try:
        result = open_issue(title, body, repo=args.repo, label=args.label, root=root)
    except RuntimeError as exc:
        print(f"❌ {exc}")
        return 1
    print(f"✅ issue created: {(result.stdout or '').strip() or title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
