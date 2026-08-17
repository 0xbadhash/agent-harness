# Spec: Outer-loop plan / tickets / plan-review + playbook

- **Product:** agent-harness
- **Created:** 2026-08-15
- **Status:** ready-for-agent
- **Priority:** P0
- **Plan:** docs/specs/2026-08-15-outer-loop-plan-tickets-review-plan.md
- **Tickets:** docs/specs/2026-08-15-outer-loop-plan-tickets-review/tickets/
- **Grill-me:** complete

## Problem Statement

Grill-me locks *what* but large ships still skip *how*, multi-PR guidance, and pre-code plan scrutiny.

## Solution

Fail-closed outer loop for large non-waiver ships (plan + tickets if steps ≥ N + PLAN_REVIEW), host playbook, plan_review skill, P0 operator grill process.

## Acceptance Criteria

- [ ] AC-1: `check_outer_loop.py` requires plan for large non-waiver ships
- [ ] AC-2: Tickets required when plan Implementation sequence ≥ N (default 4)
- [ ] AC-3: PLAN_REVIEW required when plan is required
- [ ] AC-4: hard_gates wires outer_loop
- [ ] AC-5: `docs/outer-loop-playbook.md` (design/stack + P0 grill)
- [ ] AC-6: `/plan_review` skill in ship_skills
- [ ] AC-7: Unit tests for outer loop
- [ ] AC-8: start-a-feature + grill checklist updated for P0 operator

## Grill-me

**Status:** complete  
**Date:** 2026-08-15

### G1 Outcome
- Q: Done looks like?
  - A: Large ships cannot approve without plan + plan review (+ tickets if long sequence); playbook documents design stack and P0 grill.

### G2 Non-goal / kill
- Q: Not build?
  - A: Multi-agent runtime; forcing plan on every one-line hotfix.

### G3 Wrong product
- Q: Repo?
  - A: agent-harness SoT only.

### G4 Cheapest alternative
- Q: Smaller?
  - A: Plan gate alone; still ship playbook + tickets + plan_review together as one outer-loop pack.

### G5 Abuse / failure
- Q: Failure mode?
  - A: Thin plan stubs — substance check ≥200 chars + sections; OUTER_LOOP_SKIP escape.

### G6 Verify
- Q: Prove?
  - A: unittest + pr_validator on this ship with plan/tickets/PLAN_REVIEW.

### G7 Priority
- Q: Why now?
  - A: Operator chose outer-loop next after value/confidence review.

## Out of Scope

- Graphite automation inside harness
- Cryptographic proof of human grill answers
