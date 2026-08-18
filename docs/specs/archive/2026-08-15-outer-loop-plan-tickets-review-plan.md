# Plan: Outer-loop plan / tickets / plan-review

- **Spec:** docs/specs/2026-08-15-outer-loop-plan-tickets-review.md
- **Product:** agent-harness
- **Created:** 2026-08-15
- **Status:** ready-for-agent

## Stack & constraints

Python gates + markdown skills/docs only. Reuse `review_scope.is_large_baseline`.

## Approach

Add `check_outer_loop.py`, wire into `hard_gates`, ship `plan_review` skill, playbook, docs, tests, release 1.4.30.

## Architecture decisions

- One checker module (plan + tickets + PLAN_REVIEW) to keep hard_gates simple
- Large-only by default; `OUTER_LOOP_FORCE_PLAN` for tests/ops
- Tickets threshold env `OUTER_LOOP_TICKET_STEPS` (default 4)
- plan_review is portable skill, not a pipeline phase

## File / surface map

| Area | Change |
|------|--------|
| scripts/check_outer_loop.py | New |
| scripts/hard_gates.py | Wire |
| skills/plan_review/ | New skill |
| docs/outer-loop-playbook.md | Host playbook |
| docs/start-a-feature.md | Large / P0 paths |
| grill-me-checklist.md | P0 operator |
| ship_skills.txt | plan_review |
| tests/test_check_outer_loop.py | Units |

## Implementation sequence

1. Implement check_outer_loop.py (plan/tickets/review rules + env knobs)
2. Wire outer_loop into hard_gates evaluate path
3. Add plan_review skill, outer-loop playbook, P0 grill docs
4. Add unit tests and update start-a-feature / skills-catalog
5. Ship artifacts PR_DRAFT PLAN_REVIEW code review release 1.4.30

## Testing plan

- `python3 -m unittest tests.test_check_outer_loop`
- `python3 scripts/check_outer_loop.py` on this PR with FORCE if needed
- product_smoke / pr_validator

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Threshold false positives | large_only + waiver |
| Thin plans | substance check |
| Ticket theater | ≥1 real ticket file; N=4 |
