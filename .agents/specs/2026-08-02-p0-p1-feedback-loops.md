# P0–P1 feedback loops — finish-ship, night promote, portfolio install, remaining board

- **Product:** agent-harness
- **Created:** 2026-08-02
- **Status:** ready-for-agent
- **Priority:** P0 (A1/A3, A5/A8) · P1 (A4, A2/B6)
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-08-02-p0-p1-feedback-loops-plan.md`
- **Tickets:** `.agents/specs/2026-08-02-p0-p1-feedback-loops/tickets/`
- **Tracker:** local
- **Constitution:** AGENTS.md + portable harness
- **Depends on:** v1.4.11 morning triage, hard gates, next_skill

## Problem Statement

Session inventory left four open moves:

| ID | Gap |
|----|-----|
| **A1/A3** | Operator re-types full FSM; push not proven |
| **A5/A8** | Night FAIL stays TODO; not promoted to durable checks |
| **A4** | After harness tag, products lag until manual reinstall |
| **A2/B6** | “What remaining?” has no durable board |

Morning triage (v1.4.11) only **detects**. This wave **closes** the four moves with bounded automation (no infinite invent-and-ship).

## Solution

| Ticket | Outcome |
|--------|---------|
| **01 A1/A3** | `finish_ship.py` walks NEXT_SKILL plan + **push proof** checklist artifact; docs for single finish command |
| **02 A5/A8** | `promote_night_fails.py` rolls FAIL gates → `.agents/artifacts/NIGHT_FAIL_PROMOTIONS.md` + optional stub test path under `tests/night_fail_promotions/` when gate known |
| **03 A4** | `portfolio_install_report.py` after harness release: install dry-run inventory + residual report (push products is explicit `--apply-install` opt-in, never silent force-push) |
| **04 A2/B6** | `remaining_board.py` writes `.agents/artifacts/REMAINING.md` from OPEN roadmap + night FAIL + pipeline phase |

No new FSM phases. No auto-merge. No invent greenfield features.

## User Stories

1. As an operator, I run one finish-ship helper and see whether push proof is complete.  
2. As an operator, repeated night FAIL gates become listed promotions with suggested tests, not only TODO.  
3. As a harness releaser, I get a portfolio residual report after tag.  
4. As any agent/session, I read REMAINING.md instead of re-asking “what’s left?”

## Implementation Decisions

- **A1/A3:** Script prints ordered skill checklist from `next_skill` graph + verifies `git status` clean, tag present, `git rev-parse @{u}` / `git status -sb` tracking; writes `PUSH_PROOF.md`. Does **not** spawn LLM skills automatically (CLI agent still executes skills); provides machine checklist + exit 1 if push proof fails.  
- **A5/A8:** Use taxonomy counts + last MORNING_TRIAGE / NIGHT reports; gates FAIL ≥2 products or ≥2 consecutive reports → promotion row. Stub test file only when `--write-stubs`.  
- **A4:** Default `--report-only`; `--install` runs install_into_product without git push unless `--push`.  
- **A2/B6:** Markdown board only (graph out of scope).  

## Testing Decisions

- Unit tests per script (fixtures, exit codes).  
- product_smoke green.

## Acceptance Criteria

### A1/A3
- [ ] `scripts/finish_ship.py` exists  
- [ ] Writes `.agents/artifacts/PUSH_PROOF.md` with NEXT_SKILL plan + push checks  
- [ ] Exit 0 only when clean + (optional) `--require-push` remote in sync  
- [ ] Docs in ship-flow.md  
- [ ] Tests  

### A5/A8
- [ ] `scripts/promote_night_fails.py` + NIGHT_FAIL_PROMOTIONS.md  
- [ ] Detects repeated FAIL gates across products/reports  
- [ ] `--write-stubs` creates minimal unittest placeholder for known gate names  
- [ ] Tests  

### A4
- [ ] `scripts/portfolio_install_report.py` lists products + HARNESS_VERSION vs SoT  
- [ ] Residual report when product version lagging  
- [ ] `--install` optional reinstall; `--push` separate opt-in  
- [ ] Tests  

### A2/B6
- [ ] `scripts/remaining_board.py` → REMAINING.md (OPEN roadmap + night fails + phase)  
- [ ] Tests  
- [ ] ship-flow / release_mgmt mention update board after ship  

### Cross-cutting
- [ ] CHANGELOG OPEN closed  
- [ ] No secrets; no auto-force-push  

## Out of Scope

- Auto LLM invocation of slash skills  
- Graph DB  
- Unattended execute_dev of product TODOs  
- Changing five FSM phases  

## Clarifications

### 2026-08-02 (defaults — /psec P0-P1)

- Q: Auto-run every NEXT_SKILL with subprocess LLM?  
  - A: **No** — checklist + push proof; agents still run skills.  
- Q: Auto-push all products after harness tag?  
  - A: **Report default**; install/push **opt-in flags**.  
- Q: Graph remaining board?  
  - A: **Markdown REMAINING.md only**.  

## Handoff

```text
✅ SPEC READY → /execute_dev (all tickets in one coherent release preferred)
```
