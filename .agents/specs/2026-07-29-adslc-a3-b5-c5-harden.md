# ADSLC harden — A3 ops wire-up, B5 evidence score, C5 eval runner

- **Product:** agent-harness
- **Created:** 2026-07-29
- **Status:** ready-for-agent
- **Priority:** P0 (A3, B5) · P1 (C5)
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden-plan.md`
- **Tickets:** `.agents/specs/2026-07-29-adslc-a3-b5-c5-harden/tickets/`
- **Tracker:** local
- **Constitution:** AGENTS.md + portable harness constraints
- **Depends on:** v1.4.6 ADSLC baseline + v1.4.7 front door

## Problem Statement

The first ADSLC wave (v1.4.6) delivered **code** for A3/B5/C5, but operators still hit soft gaps:

1. **A3:** Daytime readiness exists as a GHA example + cron one-liner, but there is no **installable systemd timer** parallel to `night-shift-all`, no **wiring check**, and no **product workflow template** to copy into product repos. Night shift remains the first automated multi-product signal on many hosts.
2. **B5:** Release evidence pack is **skill prose only** — hard_gates does not fail when PR_DRAFT lacks a structured evidence pack on code ships.
3. **C5:** Eval is a **markdown spike only** — no runnable checklist script operators/CI can execute for skill-conformance smoke.

## Solution

Harden only A3, B5, and C5 (no new FSM phases):

| ID | Outcome |
|----|---------|
| **A3** | Systemd unit+timer + install helper + wiring check + product GHA template; docs updated |
| **B5** | Fail-closed `## Evidence pack` (or equivalent) on code ships in `hard_gates.py` |
| **C5** | `scripts/agent_eval_checklist.py` + tests + doc promotion beyond pure spike |

## User Stories

1. As an operator, I want a daytime systemd timer I can enable like night-shift, so red products fail before 03:15 HKT.
2. As an operator, I want `check_daytime_wiring` to report missing workflow/timer pieces without guessing host secrets.
3. As a reviewer, I want hard_gates to reject code ships missing a release-style evidence pack section.
4. As a harness maintainer, I want one command that runs the C5 skill-conformance checklist and exits non-zero on fail.

## Implementation Decisions

- **No new pipeline phases.**
- **A3:** Follow `deploy/night-shift-all.*` patterns; `SuccessExitStatus=0 1` for multi-product partial fail; install script is **opt-in** (never auto-enables without operator flag).
- **B5:** Require `## Evidence pack` header in PR_DRAFT for non-prose ships; body must mention ≥2 of: hard_gates, smoke, pytest/unittest, validate, coverage, SBOM.
- **C5:** Checklist script shells out to existing tools (next_skill, hard_gates --help, fsm tests subset); not LLM-as-judge.
- Portable: no new host-only defaults in public skill text; deploy units may match existing night-shift host layout (documented).

## Testing Decisions

- Unit tests for hard_gates Evidence pack (pass/fail).
- Unit tests for agent_eval_checklist exit codes.
- Unit tests for check_daytime_wiring on fixture trees.
- Product smoke + existing hard_gates suite green.

## Acceptance Criteria

### A3

- [ ] `deploy/daytime-gates.service` + `deploy/daytime-gates.timer` call multi-product `daytime_readiness_subset.py`
- [ ] `scripts/install_daytime_timer.sh` installs units with `--dry-run` default and `--apply` to copy+enable
- [ ] `scripts/check_daytime_wiring.py` verifies harness workflow file + deploy units present; optional product roots for template presence
- [ ] `templates/daytime-gates.yml` product-copyable GHA workflow
- [ ] Docs: night-shift.md + ship-flow mention install path
- [ ] Tests for wiring check

### B5

- [ ] Code ships: hard_gates fails without `## Evidence pack` with sufficient body
- [ ] Prose-only ships skip Evidence pack
- [ ] release_mgmt skill + PR_DRAFT template mention Evidence pack shape
- [ ] Unit tests green

### C5

- [ ] `scripts/agent_eval_checklist.py` runs automated checks; exit 0 on pass
- [ ] Docs `agent-eval-spike.md` updated with runner usage (still not a full eval platform)
- [ ] Optional step in daytime-gates.yml
- [ ] Unit/smoke tests

### Cross-cutting

- [ ] CHANGELOG OPEN item closed per ticket ships
- [ ] No secrets; hard gates satisfied for each code ship
- [ ] Product smoke passes

## Out of Scope

- Enabling daytime timer on host without operator `--apply`
- Full SBOM/commercial scanners as hard deps
- LLM-as-judge transcript scoring
- Changing night_shift schedule or FSM phases
- Auto-merging product GHA workflows into all product remotes

## Clarifications

### 2026-07-29 (from conversation — recommended defaults)

- Q: Scope of this wave?
  - A: Only **A3 ops wire-up**, **B5 score**, **C5 runnable checklist** — not redoing A4/A5/B1–B4/C1–C4.
- Q: Ship one mega-PR or per ticket full FSM?
  - A: **Per ticket** full ship: execute_dev → code_review → cross_review → behavior_validator → pr_review → release_mgmt → sync_docs.
- Q: B5 fail-closed on PR_DRAFT or only RELEASE_RUNBOOK?
  - A: **PR_DRAFT at hard_gates** (score time); release_mgmt still writes RELEASE_RUNBOOK Evidence pack.
- Q: Auto-enable systemd on install?
  - A: **No** — dry-run default; `--apply` required.
- Q: C5 platform?
  - A: **Minimal runner only**; spike doc remains honest about non-goals.

## Further Notes

- Builds on v1.4.6; do not regress hard_gates=25 semantics (all-or-nothing).
- Prior OPEN ADSLC checklist in CHANGELOG can be marked DONE; this is a new OPEN item.

## Handoff

```text
✅ SPEC READY
   spec:  .agents/specs/2026-07-29-adslc-a3-b5-c5-harden.md
   plan:  .agents/specs/2026-07-29-adslc-a3-b5-c5-harden-plan.md
   tickets: .agents/specs/2026-07-29-adslc-a3-b5-c5-harden/tickets/
   next:  /execute_dev  (ticket 01 — A3)
   then:  full FSM per ticket 02 (B5), 03 (C5)
```
