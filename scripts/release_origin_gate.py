#!/usr/bin/env python3
"""Fail-closed origin gate for /release_mgmt product ships.

After a release tag, origin must have:
  1. Current HEAD commit reachable on the remote default/tracking branch
  2. Tag ``v$VERSION`` present on origin (``git ls-remote --tags``)

  python3 scripts/release_origin_gate.py --root . --push
  python3 scripts/release_origin_gate.py --root . --verify-only
  python3 scripts/release_origin_gate.py --root . --expect-tag v9.9.9  # dry miss

Exit 0 only when origin has HEAD + tag. Used by finish_ship --require-push
(auto-push then verify). Not for night-bar commits.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return int(r.returncode), ((r.stdout or "") + (r.stderr or "")).strip()


def read_version(root: Path) -> str:
    p = root / "VERSION"
    if not p.is_file():
        raise FileNotFoundError("VERSION file missing")
    return p.read_text(encoding="utf-8").strip()


def local_head(root: Path) -> str:
    rc, out = _run(["git", "rev-parse", "HEAD"], root)
    if rc != 0 or not out:
        raise RuntimeError(f"git rev-parse HEAD failed: {out}")
    return out.splitlines()[0].strip()


def tracking_ref(root: Path) -> str:
    """Prefer upstream of HEAD; else origin/main then origin/master."""
    rc, out = _run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root)
    if rc == 0 and out.startswith("origin/"):
        return out
    for cand in ("origin/main", "origin/master"):
        rc, _ = _run(["git", "rev-parse", "--verify", cand], root)
        if rc == 0:
            return cand
    return "origin/main"


def push_head_and_tags(root: Path) -> tuple[bool, list[str]]:
    msgs: list[str] = []
    # Push current branch HEAD
    rc, out = _run(["git", "push", "-u", "origin", "HEAD"], root)
    msgs.append(f"git push origin HEAD → rc={rc}")
    if out:
        msgs.append(out[-1500:])
    if rc != 0:
        return False, msgs + ["fail: git push origin HEAD"]
    # Push tags (includes v$VERSION if created)
    rc2, out2 = _run(["git", "push", "origin", "--tags"], root)
    msgs.append(f"git push origin --tags → rc={rc2}")
    if out2:
        msgs.append(out2[-1500:])
    if rc2 != 0:
        return False, msgs + ["fail: git push origin --tags"]
    return True, msgs


def fetch_origin(root: Path) -> tuple[bool, str]:
    rc, out = _run(["git", "fetch", "origin", "--tags", "--prune"], root)
    return rc == 0, out[-1500:] if out else ""


def origin_has_commit(root: Path, sha: str, remote_ref: str) -> tuple[bool, str]:
    """True if sha is an ancestor of remote_ref (branch contains our HEAD)."""
    rc, _ = _run(["git", "merge-base", "--is-ancestor", sha, remote_ref], root)
    if rc == 0:
        return True, f"ok: {sha[:12]} ⊆ {remote_ref}"
    # Also accept exact tip match
    rc2, tip = _run(["git", "rev-parse", remote_ref], root)
    if rc2 == 0 and tip.splitlines()[0].strip() == sha:
        return True, f"ok: {remote_ref} tip == HEAD"
    return False, f"fail: origin lacks HEAD {sha[:12]} on {remote_ref} (behind or unpushed)"


def origin_has_tag(root: Path, tag: str) -> tuple[bool, str]:
    """Fail-closed: tag must appear on origin via ls-remote."""
    rc, out = _run(["git", "ls-remote", "--tags", "origin", tag], root)
    if rc != 0:
        return False, f"fail: ls-remote --tags origin {tag} rc={rc} {out[-200:]}"
    # lines like: <sha>\trefs/tags/v1.2.3  or  refs/tags/v1.2.3^{}
    found = False
    for line in out.splitlines():
        if f"refs/tags/{tag}" in line and "^{}" not in line.split("\t")[-1]:
            found = True
            break
        if f"refs/tags/{tag}" in line:
            found = True
    if not found:
        return False, f"fail: origin missing tag {tag} (ls-remote empty)"
    return True, f"ok: origin has tag {tag}"


def verify(
    root: Path,
    *,
    expect_tag: str | None = None,
) -> tuple[bool, list[str]]:
    root = root.resolve()
    msgs: list[str] = []
    try:
        ver = read_version(root)
        tag = expect_tag or f"v{ver}"
        sha = local_head(root)
    except Exception as e:  # noqa: BLE001
        return False, [f"fail: {e}"]

    ok_fetch, fetch_out = fetch_origin(root)
    if not ok_fetch:
        return False, [f"fail: git fetch origin: {fetch_out}"]
    msgs.append("ok: fetched origin --tags")

    remote_ref = tracking_ref(root)
    ok_head, head_msg = origin_has_commit(root, sha, remote_ref)
    msgs.append(head_msg)
    ok_tag, tag_msg = origin_has_tag(root, tag)
    msgs.append(tag_msg)

    # Local ahead of origin after fetch → still fail closed
    rc, sb = _run(["git", "status", "-sb"], root)
    if rc == 0:
        line = sb.splitlines()[0] if sb else ""
        if "ahead" in line:
            msgs.append(f"fail: still ahead of upstream after push/fetch ({line.strip()})")
            ok_head = False

    return bool(ok_head and ok_tag), msgs


def ensure_release_on_origin(
    root: Path,
    *,
    do_push: bool = True,
    expect_tag: str | None = None,
) -> tuple[bool, list[str]]:
    """Push (optional) then fail-closed verify. Default do_push=True for release_mgmt."""
    root = root.resolve()
    msgs: list[str] = []
    if do_push:
        ok_p, pmsgs = push_head_and_tags(root)
        msgs.extend(pmsgs)
        if not ok_p:
            return False, msgs
    ok_v, vmsgs = verify(root, expect_tag=expect_tag)
    msgs.extend(vmsgs)
    return ok_v, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--push",
        action="store_true",
        help="git push origin HEAD + --tags before verify (release_mgmt default path)",
    )
    ap.add_argument(
        "--verify-only",
        action="store_true",
        help="Fetch + verify only (no push)",
    )
    ap.add_argument(
        "--expect-tag",
        default=None,
        help="Override tag name (for dry-miss tests, e.g. v0.0.0-missing)",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()
    do_push = bool(args.push) and not args.verify_only
    ok, msgs = ensure_release_on_origin(
        root, do_push=do_push, expect_tag=args.expect_tag
    )
    for m in msgs:
        pref = "✅ " if m.startswith("ok:") else ("❌ " if m.startswith("fail:") else "· ")
        print(pref + m)
    if ok:
        print("✅ release_origin_gate PASS (origin has HEAD + tag)")
        return 0
    print("❌ release_origin_gate FAIL (origin missing HEAD and/or v$VERSION)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
