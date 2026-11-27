# Plan review — harness top-50 completion

**Marker:** PLAN-REVIEW
**Spec:** `.agents/specs/2026-11-27-harness-top50-completion.md`
**Plan:** `.agents/specs/2026-11-27-harness-top50-completion-plan.md`
**Tickets:** `.agents/specs/2026-11-27-harness-top50-completion/tickets`

## Verdict

APPROVE. The plan covers all thirty-five remaining scorecard items and the two
P2 follow-ups with one ticket per mechanism. Each ticket names the script or gate
that makes the item observable, so none of the work can collapse into policy
prose. The four review chunks are balanced (860 / 1500 / 490 estimated LOC), and
the dependency layers have a real ready frontier.

## Findings

1. **Estimate realism.** The epic estimates 2,850 LOC, above the single-PR
   comfort zone. Mitigation: chunked review and one agent-harness PR plus one
   workflow-harness PR. Accepted.
2. **Advisory gates.** Feature-flag, token/cost, and comment-ratio checks report
   without failing for repos that declare no surface. Mitigation: this repo runs
   them with `--strict`. Accepted.
3. **External repo.** Batch F touches workflow-harness, whose local checkout is
   dirty from another session. Mitigation: cut a clean worktree from
   `origin/main`. Accepted.
4. **Live actions.** `--auto-merge` and `--gh` can act on GitHub. Mitigation: both
   stay opt-in and are covered by dry-run tests. Accepted.

## Gate checks

- Spec AC-1..AC-6 are checkable.
- Ticket DAG valid (19 tickets); ready frontier `01, 07, 10, 12, 16, 17`.
- Stack plan: 3 layers, 3 review chunks, no cycles or missing dependencies.
- Reserved versus delegated decisions are recorded in the spec and plan
  templates, and no decision is delegated to the agent that the operator has not
  seen.

## Handoff

✅ PLAN-REVIEW DONE
NEXT_SKILL=/execute_dev
