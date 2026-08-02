# Night-shift morning triage (auto-feedback slice 1)

- **Product:** agent-harness
- **Created:** 2026-08-02
- **Status:** ready-for-agent
- **Priority:** P0
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-08-02-night-shift-morning-triage-plan.md`
- **Tickets:** `.agents/specs/2026-08-02-night-shift-morning-triage/tickets/`
- **Tracker:** local
- **Constitution:** AGENTS.md + portable harness constraints
- **Depends on:** night_shift readiness + vault TODO writers

## Problem Statement

Overnight readiness leaves **FAIL gates and TODO checkboxes** after bounded mechanical autofix. Operators re-ask “why did night fail?” and manually hunt TODOs every morning. There is **no morning triage** that:

1. Aggregates last-night FAIL across products  
2. Optionally re-runs readiness once (bounded)  
3. Writes a single **MORNING_TRIAGE** artifact with exit code for timers/CI  

Without this, residual reds require manual effort forever.

## Solution

Add **morning triage** (not unattended full ship):

- Script scans product roots (night_shift products file) for last reports/TODOs  
- Classifies overall PASS/FAIL per product  
- Optional `--recheck`: re-run `daytime_readiness_subset` or single-product readiness once for FAIL products  
- Writes `.agents/artifacts/MORNING_TRIAGE.md` (+ optional vault summary path documented)  
- Exit **1** if any product still FAIL after recheck (or without recheck if any FAIL)  
- Deploy unit template + docs (dry-run install, like daytime-gates)  
- **No** auto `/execute_dev` / auto-ship in this slice  

## User Stories

1. As an operator, I want one command/timer after night_shift that answers “what failed?” without opening each product.  
2. As an operator, I want FAIL products re-checked once after mechanical windows, so flaky deps don’t force a chat.  
3. As an agent session, I want `MORNING_TRIAGE.md` so I don’t re-ask the same night-fail question.

## Implementation Decisions

- Reuse `config/night_shift_products.yaml` product list.  
- Parse existing `NIGHT_SHIFT_REPORT.md` / TODO “Overall: **FAIL|PASS**” patterns.  
- Recheck uses existing readiness/daytime scripts — no new gate families.  
- No new FSM phases.  
- Graph knowledge: out of scope (status file is enough for slice 1).

## Testing Decisions

- Unit tests: fixture PASS/FAIL trees → exit codes + artifact content.  
- Smoke: harness product_smoke still green.

## Acceptance Criteria

- [ ] `scripts/night_shift_morning_triage.py` exists; `--help` works  
- [ ] Scans multi-product roots; writes `MORNING_TRIAGE.md` with per-product PASS/FAIL  
- [ ] Exit 0 when all PASS; exit 1 when any FAIL  
- [ ] `--recheck` re-runs readiness once for FAIL products and updates result  
- [ ] Tests cover pass/fail/recheck fixtures  
- [ ] Docs in `docs/night-shift.md` + optional `deploy/morning-triage.*` + install dry-run  
- [ ] No secrets; no auto-ship  

## Out of Scope

- Unattended `/execute_dev` of TODO items  
- LLM-as-judge triage  
- Graph DB  
- Changing night_shift schedule  

## Clarifications

### 2026-08-02 (from conversation — defaults)

- Q: Full unattended ship of TODOs?  
  - A: **No** this slice — triage + optional recheck only.  
- Q: Graph?  
  - A: **No** — markdown artifact.  
- Q: Product #2 (news) separate?  
  - A: **Yes** — separate catalyxt spec/ship.

## Further Notes

Closes feedback-loop gap A5/A8 (detect) without inventing product features.

## Handoff

```text
✅ SPEC READY
   next: /execute_dev ticket 01
```
