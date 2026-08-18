# Spec: Night parallel + Waiting leftovers (agent-harness only)

- **Product:** agent-harness
- **Created:** 2026-08-18
- **Status:** ready-for-agent
- **Priority:** P0
- **Plan:** docs/specs/2026-08-18-night-parallel-waiting-leftovers-plan.md
- **Grill-me:** complete

## Problem Statement

Night all-products ran sequentially (sum of walls). Pane/docs leftovers: invented surface_inventory, ship_skills vs router mismatch, leftover plans, stale pipeline/SESSION_CONTEXT, duplicated schedule tables, raw ZAP HTML, optional skills required on install.

## Solution

Parallel `--jobs` for independent products; honest optional skills; real optional surface_inventory; schedule one-liner; ZAP SUMMARY; refresh context; archive leftover plans.

## Acceptance Criteria

- [ ] AC-1: night_shift_all parallel jobs; 10-product list unchanged
- [ ] AC-2: wall time reported vs CPU on dry/quick run
- [ ] AC-3: surface_inventory.py exists (declared targets; no domain-find; no night ZAP crawl)
- [ ] AC-4: stale test_trigger_schedule pytest cache cleared
- [ ] AC-5: next_skill routes /plan_review after spec when Plan linked; qa_campaign/retrospect/audit_harness optional
- [ ] AC-6: leftover *-plan.md archived; skills/plan_review is SoT
- [ ] AC-7: pipeline.json task + SESSION_CONTEXT reflect current VERSION
- [ ] AC-8: night reports link schedule SoT once (no full table copy); ZAP SUMMARY.md
- [ ] AC-9: no Graft/ECC; no ZAP in night_shift_all; no product PASS reopen

## Grill-me

**Status:** complete  
**Date:** 2026-08-18

### G1 Outcome
- Q: Done?
  - A: Parallel night + Waiting leftovers cleared honestly on harness only.

### G2 Non-goal
- Q: Kill?
  - A: Graft/ECC, domain-find, ZAP night crawl, reopening product PASSes.

### G3 Wrong product
- Q: Repo?
  - A: agent-harness window 2 only.

### G4 Cheapest
- Q: Smaller?
  - A: ThreadPool on existing run_one; no new orchestrator.

### G5 Abuse
- Q: Risk?
  - A: Vault write races — each product already writes own paths; summary after barrier.

### G6 Verify
- Q: Prove?
  - A: `--dry-run --quick` jobs=1 vs jobs=10 wall/cpu; unittest product list=10.

### G7 Priority
- Q: Why now?
  - A: CEO Waiting + overnight wall waste.

## Out of Scope

- Product portfolio reinstall (unless needed for harness SoT only — not this ship)
- Domain-find / ZAP target expansion as night crawl
