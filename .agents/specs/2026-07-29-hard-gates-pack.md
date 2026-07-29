# Hard gates pack — enforce ship evidence in pr_validator

- **Product:** agent-harness
- **Created:** 2026-07-29
- **Status:** ready-for-agent
- **Priority:** P0
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-07-29-hard-gates-pack-plan.md`
- **Tracker:** local
- **Constitution:** policy defaults + AGENTS.md

## Problem Statement

Ship quality depends on skill text (code review, TDD red-proof, behavior proof, spec linkage). Agents and operators can skip under pressure; `pr_validator` still awards ≥95 from suite + hardcodes + §9 alone. Soft gates under-deliver the designed FSM.

## Solution

`/pr_review --validate` **fails closed** on code ships unless a small set of **hard gates** pass. Operators use explicit **waivers** only for documented exceptions (hotfix / prose-only path via review_scope).

## User Stories

1. As an operator, I want score blocked when CODE-REVIEW is missing on a code ship, so unreviewed code cannot be “approved.”
2. As an operator, I want red-proof required for code ships, so “tests green” is not a substitute for TDD evidence.
3. As an operator, I want secrets-on-diff fail closed when a diff range is provided.
4. As an operator, I want BEHAVIOR-REPORT required when the ship has runtime surface (non-prose).
5. As an operator, I want **Spec:** path or **Spec waiver:** on every PR_DRAFT, so intent is linked or explicitly waived.
6. As an implementer of prose-only docs, I want heavy gates skipped when `review_scope` says prose-only.

## Implementation Decisions

- New module `scripts/hard_gates.py` — pure checks; called from `pr_validator.score`.
- Rubric: add **hard_gates** bucket (25 pts all-or-nothing); rebalance existing buckets to total 100.
- Prose-only (`review_scope.skip_heavy_review` / `prose_only`): skip CODE-REVIEW, red-proof, behavior; still require spec/waiver + §9 + hygiene.
- `--diff` optional: without diff, secrets_diff and prose detection use HEAD~1...HEAD when git available; else secrets gate warns not blocks if no range.
- Docs: ship-flow + pr_review skill + CHANGELOG.

## Testing Decisions

- Unit tests for each gate pass/fail with temp PR_DRAFT and fake artifacts.
- Integration: full `pr_validator` on fixture tree.
- Public contract: `hard_gates.evaluate(root, pr_draft, diff) -> HardGatesResult`.

## Acceptance Criteria

- [ ] Non-prose ship without CODE-REVIEW marker → hard_gates fail → score &lt; 95
- [ ] Non-prose without Red-proof / red_cmd|green_cmd|TDD section → fail
- [ ] Runtime non-prose without BEHAVIOR-REPORT marker → fail
- [ ] Missing Spec path and Spec waiver → fail
- [ ] Spec waiver `hotfix|chore|docs-only|prose-only` accepted
- [ ] Prose-only skip of CODE-REVIEW / red-proof / behavior
- [ ] Secrets findings with --diff → fail (fail closed)
- [ ] All hard gates green → 25 pts hard_gates; can reach 100 with rest
- [ ] Docs ship-flow describe hard gates; tests green; smoke green

## Out of Scope

- Changing pipeline phases
- Making `/qa_campaign` mandatory
- Forced cross_review hard by default (keep --strict-cross-review)
- Product-specific threat models / SBOM

## Clarifications

### 2026-07-29
- Q: Spec required always or waiver allowed?
  - A: **Spec path OR Spec waiver** (hotfix|chore|docs-only|prose-only) required on PR_DRAFT.
- Q: All-or-nothing hard_gates points?
  - A: Yes — 25 points only if every applicable hard gate passes.
- Q: Behavior required when?
  - A: When not prose-only and review_scope/runtime heuristic says runtime surface (same as next_skill).

## Further Notes

Chicken-and-egg: this ship’s own PR_DRAFT must satisfy hard gates to self-validate.

## Handoff

- Next: `/execute_dev` (implement hard_gates + pr_validator + tests + docs)
- Then: code_review → pr_review → release → sync_docs
