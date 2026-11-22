#!/usr/bin/env python3
"""Tier B-5: snapshot GitHub Actions daytime-gates status for OPS embedding.

Uses ``gh`` CLI when available. Offline / no-auth → warn rows only (exit 0).

  python3 scripts/github_daytime_status.py
  python3 scripts/github_daytime_status.py --markdown
  python3 scripts/github_daytime_status.py --write  # → .agents/artifacts/GITHUB_DAYTIME.md
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
PRODUCTS = HARNESS / "config" / "night_shift_products.yaml"

# product_id → gh repo (owner/name); override with GH_DAYTIME_REPOS json if needed
DEFAULT_REPOS: dict[str, str] = {
    "agent-harness": "0xbadhash/agent-harness",
    "email-detach": "0xbadhash/email-detach",
    "second-brain": "0xbadhash/second-brain",
    "catalyxt": "0xbadhash/catalyxt.ltd",
    "buzz": "0xbadhash/buzz",
    "zk": "0xbadhash/zk",
    "bip39": "0xbadhash/bip39",
    "watchlist": "0xbadhash/watchlist",
    "substack": "0xbadhash/substack",
}


def _repos() -> dict[str, str]:
    raw = os.environ.get("GH_DAYTIME_REPOS", "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass
    return dict(DEFAULT_REPOS)


def _gh_latest_workflow(repo: str, workflow: str = "daytime-gates.yml") -> dict:
    if not shutil.which("gh"):
        return {"status": "unknown", "detail": "gh not on PATH"}
    r = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            workflow,
            "--limit",
            "1",
            "--json",
            "status,conclusion,url,createdAt,displayTitle,headBranch",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "").strip()[:200]
        return {"status": "error", "detail": err or f"gh exit {r.returncode}"}
    try:
        rows = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        return {"status": "error", "detail": "bad json from gh"}
    if not rows:
        return {"status": "none", "detail": "no runs"}
    row = rows[0]
    conclusion = (row.get("conclusion") or "").lower()
    status = (row.get("status") or "").lower()
    if status == "completed":
        st = conclusion or "completed"
    else:
        st = status or "unknown"
    return {
        "status": st,
        "detail": row.get("displayTitle") or "",
        "url": row.get("url") or "",
        "branch": row.get("headBranch") or "",
        "createdAt": row.get("createdAt") or "",
    }


def local_origin_parity(root: Path = HARNESS, branch: str = "main") -> dict:
    """Compare local ``main`` with ``origin/main`` (E03 fork-drift alarm).

    Returns {ok, ahead, behind, detail}. ``ahead`` = local commits not on
    origin; ``behind`` = origin commits not local. Missing git/remote is
    reported as unknown, not green.
    """
    if shutil.which("git") is None:
        return {"ok": False, "ahead": 0, "behind": 0, "detail": "git not on PATH"}
    ref = f"origin/{branch}"
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return {"ok": False, "ahead": 0, "behind": 0, "detail": f"{ref} not found"}
    counts = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--left-right", "--count", f"{ref}...{branch}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if counts.returncode != 0:
        return {
            "ok": False,
            "ahead": 0,
            "behind": 0,
            "detail": (counts.stderr or "rev-list failed").strip()[:200],
        }
    try:
        behind_s, ahead_s = (counts.stdout or "").split()
        behind, ahead = int(behind_s), int(ahead_s)
    except ValueError:
        return {"ok": False, "ahead": 0, "behind": 0, "detail": "bad rev-list output"}
    ok = ahead == 0 and behind == 0
    detail = (
        f"in sync with {ref}"
        if ok
        else f"DRIFT: ahead {ahead}, behind {behind} vs {ref}"
    )
    return {"ok": ok, "ahead": ahead, "behind": behind, "detail": detail}


def parity_alert(parity: dict) -> str:
    """Loud, non-silent escalation text for a diverged checkout."""
    if parity.get("ok"):
        return "✅ local main ↔ origin/main: in sync"
    return (
        "🚨 ALERT — fork drift: "
        + str(parity.get("detail") or "unknown")
        + " — fetch/rebase, or open a fork-sync issue before trusting this status"
    )


def collect() -> list[dict]:
    out: list[dict] = []
    for pid, repo in sorted(_repos().items()):
        info = _gh_latest_workflow(repo)
        out.append({"product": pid, "repo": repo, **info})
    return out


def render_markdown(rows: list[dict], parity: dict | None = None) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# GitHub daytime-gates status (Tier B-5)",
        "",
        f"_Generated {now} by `scripts/github_daytime_status.py`_",
        "",
    ]
    if parity is not None:
        lines.extend(["## Local ↔ origin parity", "", parity_alert(parity), ""])
    lines.extend(
        [
            "| Product | Repo | Status | Branch | Link |",
            "|---------|------|--------|--------|------|",
        ]
    )
    for r in rows:
        url = r.get("url") or ""
        link = f"[run]({url})" if url else "—"
        lines.append(
            f"| {r.get('product')} | `{r.get('repo')}` | **{r.get('status')}** | "
            f"{r.get('branch') or '—'} | {link} |"
        )
    lines.extend(
        [
            "",
            "> **Act:** red/failure → open Link, fix, push. Green here ≠ night PASS.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--markdown", action="store_true", default=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument(
        "--out",
        type=Path,
        default=HARNESS / ".agents" / "artifacts" / "GITHUB_DAYTIME.md",
    )
    ap.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit 1 when local main and origin/main diverge (default: alert only)",
    )
    args = ap.parse_args(argv)
    rows = collect()
    parity = local_origin_parity()
    if not parity["ok"]:
        print(parity_alert(parity), file=sys.stderr)
    if args.json:
        print(json.dumps({"rows": rows, "parity": parity}, indent=2))
    else:
        md = render_markdown(rows, parity)
        print(md)
        if args.write:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(md, encoding="utf-8")
            print(f"✅ wrote {args.out}", file=sys.stderr)
    if args.fail_on_drift and not parity["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
