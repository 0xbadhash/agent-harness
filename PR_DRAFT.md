# PR Draft — outer-loop plan / tickets / plan-review

**Spec:** docs/specs/2026-08-15-outer-loop-plan-tickets-review.md  
**Plan:** docs/specs/2026-08-15-outer-loop-plan-tickets-review-plan.md  
**Tickets:** docs/specs/2026-08-15-outer-loop-plan-tickets-review/tickets/  
**Version target:** 1.4.30  

## What Problem This Solves

Large non-waiver ships could pass grill without technical plan, multi-PR guidance, tickets, or pre-code plan review.

## Why This Change Was Made

Operator-selected outer-loop package: plan fail-closed, playbook, tickets ≥N, plan_review, P0 human grill process.

## User Impact

- Large ships: need Plan + PLAN_REVIEW (+ tickets if sequence ≥4)  
- Host design/stack documented in outer-loop-playbook  
- P0 grill: operator stays on G1–G3  

## Red-proof

- red_cmd: `python3 -c "import sys; sys.exit(1)"`
- green_cmd: `python3 -m unittest tests.test_check_outer_loop -v`

## Traceability

| AC | Evidence |
|----|----------|
| AC-1 | check_outer_loop.py + test_large_needs_plan |
| AC-2 | tickets when steps ≥ N + test_tickets_required |
| AC-3 | PLAN_REVIEW + test_large_with_plan_and_review |
| AC-4 | hard_gates outer_loop wire |
| AC-5 | docs/outer-loop-playbook.md |
| AC-6 | skills/plan_review + ship_skills |
| AC-7 | tests.test_check_outer_loop |
| AC-8 | start-a-feature + grill-me-checklist P0 |

## Threat notes

- authz: N/A docs/gates  
- secrets: none; OUTER_LOOP_SKIP is ops escape only  

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | outer_loop + existing |
| smoke | product_smoke |
| unittest | test_check_outer_loop |
| plan review | .agents/artifacts/PLAN_REVIEW.md |

## Things that look bad but are actually fine

1. OUTER_LOOP_SKIP exists — emergency only  
2. Plan review can still be thin prose (same class as CODE-REVIEW floor)  
3. Multi-PR design not automated — playbook intentional  
4. Small ships skip outer loop — by design  
