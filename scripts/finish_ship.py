#!/usr/bin/env python3
"""A1/A3 — finish-ship checklist + push proof (does not invoke LLM skills).

Prints the ordered NEXT_SKILL plan from current phase, verifies git cleanliness
and optional remote sync, writes .agents/artifacts/PUSH_PROOF.md.

  python3 scripts/finish_ship.py
  python3 scripts/finish_ship.py --require-push   # fail if ahead/behind origin
  python3 scripts/finish_ship.py --root /path/to/product

Exit 0 when proof ok (and push ok if required). Exit 1 on gaps.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Canonical post-implement skill order (agents still run each skill)
SKILL_CHAIN = [
    "code_review",
    "cross_review",
    "behavior_validator",
    "pr_review --validate",
    "release_mgmt",
    "sync_docs",
    "git push origin HEAD --tags",
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
        return ["release_mgmt", "sync_docs", "git push origin HEAD --tags"]
    if phase == "shipped":
        return ["sync_docs (if not done)", "git push origin HEAD --tags"]
    return list(SKILL_CHAIN)


def evaluate(root: Path, *, require_push: bool = False) -> PushProof:
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
            missing.append("local commits not pushed (git push)")
        elif "behind" in line:
            remote_sync = "behind"
            missing.append("remote ahead — pull/rebase before push proof")
        else:
            remote_sync = "ok"

    # tag hint: VERSION or latest tag
    has_tag = False
    ver = root / "VERSION"
    if ver.is_file():
        v = ver.read_text(encoding="utf-8").strip()
        rc, tags = _run(["git", "tag", "-l", f"v{v}"], root)
        has_tag = bool(tags.strip())
        if phase in ("shipped", "approved") and not has_tag:
            notes.append(f"VERSION={v} but tag v{v} not found (ok if not yet released)")
    else:
        notes.append("no VERSION file")

    if require_push and remote_sync != "ok":
        if "remote not in sync" not in " ".join(missing):
            missing.append(f"require-push: remote_sync={remote_sync}")

    # Artifacts that score often needs
    for rel, label in (
        ("PR_DRAFT.md", "PR_DRAFT.md"),
        (".agents/artifacts/CODE_REVIEW.md", "CODE_REVIEW (code ships)"),
    ):
        if not (root / rel).exists() and phase in ("ready_for_review", "approved"):
            notes.append(f"optional check: missing {label}")

    ok = len(missing) == 0 if require_push else (not dirty and remote_sync in ("ok", "ahead", "no_upstream", "unknown"))
    if require_push:
        ok = len([m for m in missing if "dirty" in m or "push" in m or "require-push" in m or "behind" in m or "diverged" in m or "remote" in m]) == 0 and not dirty and remote_sync == "ok"
    else:
        # soft: dirty fails; ahead is warning not fail without --require-push
        ok = not dirty
        if remote_sync == "ahead":
            notes.append("ahead of origin — run git push for full closeout (or --require-push)")

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
    ap.add_argument("--require-push", action="store_true")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    proof = evaluate(root, require_push=args.require_push)
    path = write_artifact(root, proof)
    print(f"finish_ship ok={proof.ok} phase={proof.phase} remote={proof.remote_sync} out={path}")
    for step in proof.plan:
        print(f"  PLAN: {step}")
    for m in proof.missing:
        print(f"  ❌ {m}")
    return 0 if proof.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
