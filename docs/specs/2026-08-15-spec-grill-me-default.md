# Spec: Grill-me interview mandatory by default in `/spec`

- **Product:** agent-harness
- **Created:** 2026-08-15
- **Status:** ready-for-agent
- **Priority:** P0
- **Plan:** `docs/specs/2026-08-15-spec-grill-me-default-plan.md`
- **Tickets:** `docs/specs/2026-08-15-spec-grill-me-default/tickets/`
- **Constitution:** policy defaults + ship-flow (spec required for features)

## Problem Statement

Operators prefer answering sharp questions over shipping the **wrong product or feature**. Today `/spec` allows `--no-interview` / `--no-clarify` and treats clarify as soft; agents often skip to draft AC. Grill-me is documented in provenance but not forced.

## Solution

`/spec` **always** runs a **grill-me** adversarial interview by default (one question at a time, recommended defaults). Specs cannot reach `ready-for-agent` without a `## Grill-me` evidence section (unless explicit `--spike` with reason). Optional `--plan` / `--tickets` remain available after grill + clarify.

## User Stories

1. As an operator, I want the agent to **grill my idea** before coding, so I catch wrong-product / wrong-scope early.
2. As an operator, I want **one question at a time** with a recommended answer, so decisions are fast and auditable.
3. As a ship closer, I want **grill evidence in the Spec file**, so hard gates can fail closed on empty “specs.”

## Implementation Decisions

- Grill is **mandatory** on `/spec` (not a separate skill).
- `--no-interview` / `--no-clarify` **removed** as free skips; only `--spike` skips grill (must document).
- Clarify remains after draft; grill themes may run pre-draft and post-draft (gaps only).
- Deterministic check: `scripts/check_spec_grill.py` + hook from `spec_gate` / hard_gates when Spec path present (non-waiver).

## Testing Decisions

- Unit tests for grill evidence parser (complete / missing / spike-skipped).
- Skill text asserts grill-me default in SKILL.md + start-a-feature docs.

## Acceptance Criteria

- [ ] AC-1: `/spec` skill documents grill-me as **default required** (not optional flag)
- [ ] AC-2: `references/grill-me-checklist.md` exists with G1–G7 themes
- [ ] AC-3: Spec template includes `## Grill-me` section
- [ ] AC-4: `--no-interview` / `--no-clarify` no longer advertised as normal skips; `--spike` only
- [ ] AC-5: `check_spec_grill.py` fails closed when linked Spec lacks grill evidence (non-waiver)
- [ ] AC-6: Docs: start-a-feature + skills-catalog mention mandatory grill-me
- [ ] AC-7: Plan + tickets written for this ship
- [ ] AC-8: Unit tests for grill check pass

## Out of Scope

- Host-level Grok `/design` multi-agent writer loop
- Multi-agent runtime
- Forcing `--plan` / `--tickets` on every ship (still flags)
- Changing Spec waiver types for hotfix/chore

## Grill-me

**Status:** complete  
**Date:** 2026-08-15

### G1 Outcome
- Q: What does done look like?
  - A: `/spec` always grills; wrong features harder to ship without Q&A evidence.
  - Recommended was: same

### G2 Non-goal / kill
- Q: What must we not build?
  - A: No separate multi-agent design orchestrator; no forcing plan/tickets always.
  - Recommended was: same

### G3 Wrong product
- Q: Is this the right repo?
  - A: agent-harness SoT skills — yes (portable to products via install).

### G4 Cheapest alternative
- Q: Smallest ship?
  - A: Skill text + checklist + template + check_spec_grill + docs (this PR).

### G5 Abuse / failure
- Q: How could this fail operators?
  - A: Too many questions → cap themes; `--spike` for true spikes only.

### G6 Verify
- Q: How prove?
  - A: unittest check_spec_grill + skill file presence tests.

### G7 Priority
- Q: Why now?
  - A: Operator preference after night-shift outer-loop review — P0 process quality.

## Clarifications

### 2026-08-15
- Q: Plan and tickets required for this ship?
  - A: Yes (`--plan --tickets` requested).
- Q: Opt-out path?
  - A: `--spike` with reason only; Spec waiver unchanged for hotfix/chore outside full `/spec`.

## Further Notes

Aligns with “prefer answering questions over wrong products.”

## Handoff

- Next: implement tickets 01→03 then `/execute_dev` closeout already in progress in this session
- Then: pr_review → release as needed
