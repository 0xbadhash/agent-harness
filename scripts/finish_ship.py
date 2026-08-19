#!/usr/bin/env python3
"""A1/A3 — finish-ship checklist + push proof (does not invoke LLM skills).

Prints the ordered NEXT_SKILL plan from current phase, verifies git cleanliness
and optional remote sync, writes .agents/artifacts/PUSH_PROOF.md.

  python3 scripts/finish_ship.py
  python3 scripts/finish_ship.py --require-push
      # auto-push HEAD + tags, then fail-closed if origin lacks HEAD or v$VERSION
  python3 scripts/finish_ship.py --root /path/to/product

Exit 0 when proof ok (and origin gate ok if --require-push). Exit 1 on gaps.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

# Canonical post-implement skill order (agents still run each skill)
SKILL_CHAIN = [
    "code_review",
    "cross_review",
    "behavior_validator",
    "pr_review --validate",
    "release_mgmt",
    "sync_docs",
    "finish_ship --require-push  # auto-push + origin HEAD/tag gate",
]


@dataclass
class PushProof:
    ok: bool
    phase: str
    dirty: bool
    branch: str
    remote_sync: str  # ok | ahead | behind | diverged | no_upstream | unknown
    has_tag_hint: bool
    missing: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    return int(r.returncode), (r.stdout or "") + (r.stderr or "")


def _pipeline_phase(root: Path) -> str:
    p = root / ".agents" / "state" / "pipeline.json"
    if not p.is_file():
        return "unknown"
    try:
        return str(json.loads(p.read_text(encoding="utf-8")).get("phase") or "unknown")
    except json.JSONDecodeError:
        return "unknown"


def _plan_for_phase(phase: str) -> list[str]:
    """Remaining skills for operator/agent from current phase."""
    phase = (phase or "init").lower()
    if phase in ("init", "blocked"):
        return ["execute_dev", *SKILL_CHAIN]
    if phase == "ready_for_review":
        return list(SKILL_CHAIN)
    if phase == "approved":
        return [
            "release_mgmt",
            "sync_docs",
            "finish_ship --require-push",
        ]
    if phase == "shipped":
        return ["sync_docs (if not done)", "finish_ship --require-push"]
    return list(SKILL_CHAIN)


def evaluate(
    root: Path,
    *,
    require_push: bool = False,
    skip_origin_push: bool = False,
) -> PushProof:
    root = root.resolve()
    phase = _pipeline_phase(root)
    plan = _plan_for_phase(phase)
    missing: list[str] = []
    notes: list[str] = []

    rc, out = _run(["git", "status", "--porcelain"], root)
    dirty = bool(out.strip()) if rc == 0 else True
    if dirty:
        missing.append("working tree dirty (commit or stash before push proof)")

    rc, branch_out = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    branch = branch_out.strip() if rc == 0 else "unknown"

    remote_sync = "unknown"
    rc, sb = _run(["git", "status", "-sb"], root)
    if rc == 0:
        line = sb.splitlines()[0] if sb else ""
        if "..." not in line and "origin" not in line:
            remote_sync = "no_upstream"
        elif "ahead" in line and "behind" in line:
            remote_sync = "diverged"
        elif "ahead" in line:
            remote_sync = "ahead"
            if not require_push:
                missing.append("local commits not pushed (git push)")
        elif "behind" in line:
            remote_sync = "behind"
            missing.append("remote ahead — pull/rebase before push proof")
        else:
            remote_sync = "ok"

    # tag hint: VERSION or latest tag
    has_tag = False
    ver = root / "VERSION"
    version = ""
    if ver.is_file():
        version = ver.read_text(encoding="utf-8").strip()
        rc, tags = _run(["git", "tag", "-l", f"v{version}"], root)
        has_tag = bool(tags.strip())
        if phase in ("shipped", "approved") and not has_tag:
            notes.append(f"VERSION={version} but tag v{version} not found (ok if not yet released)")
    else:
        notes.append("no VERSION file")

    # Fail-closed origin gate: auto-push HEAD+tags then verify ls-remote
    if require_push and not dirty:
        try:
            from release_origin_gate import ensure_release_on_origin  # type: ignore

            do_push = not skip_origin_push
            ok_gate, gate_msgs = ensure_release_on_origin(root, do_push=do_push)
            for gm in gate_msgs:
                notes.append(gm)
            if not ok_gate:
                missing.append(
                    "require-push: origin missing HEAD and/or "
                    f"v{version or '?'} (release_origin_gate FAIL)"
                )
            else:
                # refresh remote_sync after successful push
                rc, sb = _run(["git", "status", "-sb"], root)
                if rc == 0:
                    line = sb.splitlines()[0] if sb else ""
                    if "ahead" in line and "behind" in line:
                        remote_sync = "diverged"
                    elif "ahead" in line:
                        remote_sync = "ahead"
                    elif "behind" in line:
                        remote_sync = "behind"
                    else:
                        remote_sync = "ok"
                notes.append("ok: release_origin_gate PASS")
        except Exception as e:  # noqa: BLE001
            missing.append(f"require-push: release_origin_gate error: {e}")
    elif require_push and dirty:
        missing.append("require-push: cannot push/verify while dirty")

    # Artifacts that score often needs
    for rel, label in (
        ("PR_DRAFT.md", "PR_DRAFT.md"),
        (".agents/artifacts/CODE_REVIEW.md", "CODE_REVIEW (code ships)"),
    ):
        if not (root / rel).exists() and phase in ("ready_for_review", "approved"):
            notes.append(f"optional check: missing {label}")

    if require_push:
        ok = not dirty and len(missing) == 0 and remote_sync == "ok"
    else:
        # soft: dirty fails; ahead is warning not fail without --require-push
        ok = not dirty
        if remote_sync == "ahead":
            notes.append(
                "ahead of origin — /release_mgmt must finish_ship --require-push "
                "(auto-push + fail-closed origin gate)"
            )

    return PushProof(
        ok=ok,
        phase=phase,
        dirty=dirty,
        branch=branch,
        remote_sync=remote_sync,
        has_tag_hint=has_tag,
        missing=missing,
        plan=plan,
        notes=notes,
    )


def write_artifact(root: Path, proof: PushProof) -> Path:
    out = root / ".agents" / "artifacts" / "PUSH_PROOF.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# PUSH_PROOF",
        "",
        f"_Generated {now} by finish_ship.py_",
        "",
        f"**ok:** `{proof.ok}`",
        f"**phase:** `{proof.phase}`",
        f"**branch:** `{proof.branch}`",
        f"**dirty:** `{proof.dirty}`",
        f"**remote_sync:** `{proof.remote_sync}`",
        f"**tag_hint:** `{proof.has_tag_hint}`",
        "",
        "## NEXT_SKILL plan (run in order — agent executes skills)",
        "",
    ]
    for i, step in enumerate(proof.plan, 1):
        lines.append(f"{i}. `{step}`")
    lines.extend(["", "## Missing / blockers", ""])
    if proof.missing:
        for m in proof.missing:
            lines.append(f"- ❌ {m}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Notes", ""])
    for n in proof.notes or ["—"]:
        lines.append(f"- {n}")
    lines.extend(
        [
            "",
            "## Operator",
            "",
            "```bash",
            "python3 scripts/finish_ship.py",
            "python3 scripts/finish_ship.py --require-push",
            "# After each skill: python3 scripts/next_skill.py --after <skill>",
            "```",
            "",
            "This tool does **not** auto-invoke LLM slash skills.",
            "",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--require-push",
        action="store_true",
        help="Auto-push HEAD+tags then fail-closed if origin lacks HEAD or v$VERSION",
    )
    ap.add_argument(
        "--skip-origin-push",
        action="store_true",
        help="With --require-push: verify only (no git push) — for dry-miss tests",
    )
    args = ap.parse_args(argv)
    root = args.root.resolve()
    proof = evaluate(
        root,
        require_push=args.require_push,
        skip_origin_push=bool(args.skip_origin_push),
    )
    path = write_artifact(root, proof)
    print(f"finish_ship ok={proof.ok} phase={proof.phase} remote={proof.remote_sync} out={path}")
    for step in proof.plan:
        print(f"  PLAN: {step}")
    for m in proof.missing:
        print(f"  ❌ {m}")
    for n in proof.notes:
        if n.startswith("ok:") or n.startswith("fail:"):
            print(f"  · {n}")
    return 0 if proof.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
