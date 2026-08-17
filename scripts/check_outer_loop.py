#!/usr/bin/env python3
"""Outer-loop gates: plan (large ships), tickets (≥N plan steps), plan review.

Non-waiver feature ships that are **large** (review_scope thresholds) must:

1. Link a technical plan (``**Plan:** path`` in PR_DRAFT and/or Spec).
2. If the plan's Implementation sequence has ≥ N steps (default 4), link a
   tickets directory with ≥1 ticket file.
3. Carry pre-code plan review evidence in ``.agents/artifacts/PLAN_REVIEW.md``.

Small ships and Spec waivers skip. Override with env::

  OUTER_LOOP_FORCE_PLAN=1     # require plan even if not large
  OUTER_LOOP_TICKET_STEPS=4   # N for tickets
  OUTER_LOOP_SKIP=1           # emergency skip (logs warn)

Usage::

  python3 scripts/check_outer_loop.py --root .
  python3 scripts/check_outer_loop.py --root . --base HEAD~3 --head HEAD
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

SPEC_RE = re.compile(r"\*\*Spec:\*\*\s*(\S+)", re.I)
PLAN_RE = re.compile(r"\*\*Plan:\*\*\s*(\S+)", re.I)
TICKETS_RE = re.compile(r"\*\*Tickets:\*\*\s*(\S+)", re.I)
WAIVER_RE = re.compile(
    r"\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)\b",
    re.I,
)
IMPL_SEQ_RE = re.compile(
    r"^##\s+Implementation sequence\b(.*?)(?=^##\s|\Z)",
    re.I | re.M | re.S,
)
STEP_RE = re.compile(r"^\s*\d+\.\s+\S", re.M)
PLAN_REVIEW_MARKER = "PLAN-REVIEW"
PLAN_REVIEW_MIN = 160


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _ticket_n() -> int:
    raw = os.environ.get("OUTER_LOOP_TICKET_STEPS", "4").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 4


def _resolve(root: Path, rel: str) -> Path | None:
    rel = rel.strip().strip("`")
    if rel.lower() in {"none", "n/a", "na", "-"}:
        return None
    p = (root / rel).resolve()
    if str(p).startswith(str(root.resolve())) and p.exists():
        return p
    return None


def _is_large(root: Path, base: str, head: str) -> tuple[bool, str]:
    try:
        from review_scope import build_baseline, is_large_baseline  # type: ignore

        b = build_baseline(root, base=base, head=head)
        large, detail = is_large_baseline(b, product_root=root)
        return bool(large), str(detail or "large")
    except Exception as e:  # noqa: BLE001
        # Fail open on tooling errors only when not forcing plan
        if _env_truthy("OUTER_LOOP_FORCE_PLAN"):
            return True, f"force_plan (scope error: {e})"
        return False, f"scope unavailable: {e}"


def _count_plan_steps(plan_text: str) -> int:
    m = IMPL_SEQ_RE.search(plan_text)
    body = m.group(1) if m else plan_text
    return len(STEP_RE.findall(body))


def _plan_substance(plan_text: str) -> bool:
    if len(plan_text.strip()) < 200:
        return False
    return bool(
        re.search(r"^##\s+(Approach|Architecture|Implementation)", plan_text, re.I | re.M)
    )


def _plan_review_ok(root: Path) -> tuple[bool, str]:
    path = root / ".agents" / "artifacts" / "PLAN_REVIEW.md"
    if not path.is_file():
        return False, "missing .agents/artifacts/PLAN_REVIEW.md"
    text = path.read_text(encoding="utf-8", errors="replace")
    if PLAN_REVIEW_MARKER not in text and "PLAN_REVIEW" not in text:
        return False, "PLAN_REVIEW.md missing PLAN-REVIEW marker"
    if len(text.strip()) < PLAN_REVIEW_MIN:
        return False, f"PLAN_REVIEW body < {PLAN_REVIEW_MIN} chars"
    low = text.lower()
    if not any(w in low for w in ("verdict", "approve", "reject", "pass", "fail", "finding")):
        return False, "PLAN_REVIEW missing verdict/findings language"
    return True, "ok"


def check(
    root: Path,
    pr_draft: Path,
    *,
    base: str = "HEAD~1",
    head: str = "HEAD",
) -> tuple[bool, list[str]]:
    root = root.resolve()
    msgs: list[str] = []

    if _env_truthy("OUTER_LOOP_SKIP"):
        return True, ["ok: OUTER_LOOP_SKIP set — outer loop gates skipped"]

    if not pr_draft.is_file():
        return True, ["ok: no PR_DRAFT — outer loop N/A"]

    draft = pr_draft.read_text(encoding="utf-8", errors="replace")
    if WAIVER_RE.search(draft):
        return True, ["ok: Spec waiver — outer loop plan/tickets/plan-review skipped"]

    large, large_detail = _is_large(root, base, head)
    force = _env_truthy("OUTER_LOOP_FORCE_PLAN")
    need_plan = large or force
    if not need_plan:
        return True, [f"ok: outer loop N/A (not large: {large_detail})"]

    # Resolve Spec + Plan
    sm = SPEC_RE.search(draft)
    spec_path: Path | None = None
    if sm:
        spec_path = _resolve(root, sm.group(1))

    plan_rel = None
    pm = PLAN_RE.search(draft)
    if pm:
        plan_rel = pm.group(1)
    elif spec_path and spec_path.is_file():
        sp = PLAN_RE.search(spec_path.read_text(encoding="utf-8", errors="replace"))
        if sp:
            plan_rel = sp.group(1)

    if not plan_rel:
        return False, [
            f"fail: large ship ({large_detail}) needs **Plan:** path in PR_DRAFT "
            "or Spec frontmatter (technical how; see docs/outer-loop-playbook.md)"
        ]

    plan_path = _resolve(root, plan_rel)
    if plan_path is None or not plan_path.is_file():
        return False, [f"fail: Plan path missing: {plan_rel}"]

    plan_text = plan_path.read_text(encoding="utf-8", errors="replace")
    if not _plan_substance(plan_text):
        return False, [
            f"fail: Plan too thin ({plan_rel}) — need Approach/Architecture/"
            "Implementation sequence and ≥200 chars"
        ]
    msgs.append(f"ok: plan present ({plan_rel})")

    # Tickets when steps ≥ N
    n_steps = _count_plan_steps(plan_text)
    n_need = _ticket_n()
    if n_steps >= n_need:
        t_rel = None
        tm = TICKETS_RE.search(draft)
        if tm:
            t_rel = tm.group(1)
        elif spec_path and spec_path.is_file():
            st = TICKETS_RE.search(
                spec_path.read_text(encoding="utf-8", errors="replace")
            )
            if st:
                t_rel = st.group(1)
        if not t_rel and plan_path:
            # convention: sibling tickets/ under slug
            cand = plan_path.parent / plan_path.stem.replace("-plan", "") / "tickets"
            if not cand.is_dir():
                # docs/specs/YYYY-slug-plan.md → docs/specs/YYYY-slug/tickets
                stem = plan_path.stem
                if stem.endswith("-plan"):
                    cand = plan_path.parent / stem[: -len("-plan")] / "tickets"
            if cand.is_dir():
                t_rel = str(cand.relative_to(root))
        if not t_rel:
            return False, [
                f"fail: plan has {n_steps} implementation steps (≥{n_need}) — "
                "add **Tickets:** dir with ≥1 ticket (or shrink sequence)"
            ]
        t_path = _resolve(root, t_rel)
        if t_path is None or not t_path.is_dir():
            return False, [f"fail: Tickets path missing: {t_rel}"]
        tickets = list(t_path.glob("*.md")) + list(t_path.glob("**/*.md"))
        if not tickets:
            return False, [f"fail: Tickets dir empty: {t_rel}"]
        msgs.append(f"ok: tickets ({t_rel}, {len(tickets)} file(s), steps={n_steps})")
    else:
        msgs.append(f"ok: tickets N/A (plan steps {n_steps} < {n_need})")

    # Pre-code plan review (required when plan is required)
    pr_ok, pr_detail = _plan_review_ok(root)
    if not pr_ok:
        return False, msgs + [
            f"fail: pre-code plan review — {pr_detail} "
            "(write .agents/artifacts/PLAN_REVIEW.md with marker PLAN-REVIEW)"
        ]
    msgs.append(f"ok: plan review ({pr_detail})")
    return True, msgs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--pr-draft", type=Path, default=None)
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    draft = args.pr_draft or (root / "PR_DRAFT.md")
    ok, msgs = check(root, draft, base=args.base, head=args.head)
    for m in msgs:
        pref = "✅ " if m.startswith("ok:") else ("❌ " if m.startswith("fail:") else "⚠️  ")
        print(pref + m)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
