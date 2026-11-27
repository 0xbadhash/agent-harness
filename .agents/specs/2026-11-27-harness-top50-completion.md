# Harness top-50 completion — decisions, prototype, review rigor, retro, stacked execution

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-27-harness-top50-completion-plan.md`
- **Tickets:** `.agents/specs/2026-11-27-harness-top50-completion/tickets`
- **Tracker:** local
- **Constitution:** AGENTS.md
- **Grill-me:** complete

## Problem Statement

The harness covers most of the fifty improvements ranked in the 2026-11-21
scorecard, but thirty-five items still have no wired mechanism: decisions have no
ADR spine, the grill has no prototype or handoff artifact, review has no comment
policy or process lens, retros do not read transcripts or PR comments, and a
stack cannot be merged or run ticket-by-ticket without an operator driving every
step. Operators pay for this in repeated context loss and uneven review depth.

## Solution

Each missing item becomes a small, checkable mechanism that the existing skills
call at the moment it matters: `/spec` reads and records decisions, prototypes
answer shape questions, review reports comment ratio and process signals, retro
ingests transcripts and PR comments into classified actions, and scripts merge a
stack or run the ticket frontier. Every mechanism is gated or tested so it cannot
silently rot.

## User Stories

1. As an operator, I want relevant ADRs read before the grill and new ADRs
   proposed only for hard-to-reverse decisions, so the interview does not
   relitigate settled choices.
2. As an operator, I want a prototype for shape questions and a fidelity check
   at review, so throwaway code never ships and the chosen shape is visible.
3. As a reviewer, I want a comment policy, a comment ratio, and a process lens,
   so review depth is consistent and cheap to audit.
4. As an operator, I want a compact grill handoff and a research subagent, so I
   can go AFK without losing decisions or spending the interview waiting.
5. As a maintainer, I want retros to read sessions and PR comments and classify
   findings into action classes, so improvements become issues instead of prose.
6. As an operator, I want a stack merger and a parallel ticket runner, so a large
   ship lands in order without manual babysitting.
7. As a workflow maintainer, I want ADRs, run-record retros, a canary gate, and
   an ordered stack with the registry last, so workflow changes are auditable.

## Implementation Decisions

- New mechanisms live in `scripts/` with unit tests under `tests/`.
- Skill text changes are one rule per stage; every rule names the script or gate
  that enforces it.
- `.agents/decisions/` is the ADR source of truth for this repo; skills read it
  and `check_adr.py` validates it.
- Review tiers key off the existing `**Door:**` field; no new classification.
- Feature-flag, token/cost, and comment-ratio gates are advisory when a repo
  declares no product surface.
- The workflow-harness companion ships as a separate PR from a clean worktree.

## Testing Decisions

- External behavior only: script exit codes, emitted artifacts, and skill text
  assertions that the wired command exists.
- Seams: `check_adr.py`, `check_prototype_fidelity.py`, `check_comment_audit.py`,
  `session_context.py`, `retro_job.py`, `merge_stack.py`, `run_tickets.py`,
  `check_docs_patterns.py`, `stack_plan.py`, `check_ticket_dag.py`.
- Commands: `pytest tests/ -q`, `scripts/smoke_unit.sh`, `scripts/validate.py full`.
- No browser surface: this product declares `traits.web: false`.

## Acceptance Criteria

- [ ] AC-1 (Batch A): `.agents/decisions/` exists with index and template,
  `check_adr.py` validates it, `/spec` requires an ADR read and states reserved
  versus delegated decisions, review tiers key off `**Door:**`, and a
  shared-component ticket without a prefactor fails the ticket DAG check.
- [ ] AC-2 (Batch B): a prototype skill exists, spec/PR templates carry prototype
  fields, `check_prototype_fidelity.py` fails on copied prototype code, the grill
  handoff artifact is produced, `/spec` names a read-only research subagent and a
  batch/serial mode switch, and the plan template derives a term-to-entity table.
- [ ] AC-3 (Batch C): comment policy and audit skill exist, the ratio is reported
  by code review, JS/TS ratchet template exists, the handoff token threshold and
  session cost artifact exist, cross review has a Process lens, a defect fix
  requires `repro_cmd`, and a docs-pattern check blocks rejected patterns.
- [ ] AC-4 (Batch D): `retro_job.py --transcripts` and `--pr-comments` produce
  redacted evidence, and every finding carries one of five action classes.
- [ ] AC-5 (Batch E): `merge_stack.py` merges in order and stops on red,
  `run_tickets.py` runs the unblocked frontier in parallel with per-ticket
  sessions, `stack_plan.py` accepts `--default-estimate`, and the CI ticket-DAG
  step scans every ticket root.
- [ ] AC-6 (Batch F): workflow-harness has an ADR folder, a run-record retro, a
  canary gate, and an ordered-stack rule with the registry change last.
- [ ] `python3 scripts/validate.py full` succeeds and no secrets are committed.

## Out of Scope

- Editing any product tree or `zk-business-card`.
- Creating live GitHub issues or enabling auto-merge by default.
- Changing the existing five shipped mechanisms beyond the one-line wiring the
  new rules require.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: What does the operator get when this lands?
  - A: Every remaining scorecard item is a wired mechanism with a test, and a
    large ship can run from spec to tag without manual stack surgery.

### G2 Non-goal / kill
- Q: What are we explicitly not doing?
  - A: No product-tree edits, no live issue creation, no default auto-merge, and
    no new product surface.

### G3 Wrong product
- Q: How could this be the wrong thing?
  - A: If it becomes policy prose with no checker attached. Each ticket names a
    script or gate that fails closed.

### G4 Cheapest alternative
- Q: What is the cheapest version that still helps?
  - A: Wire the existing helpers (`prototype_variants.py`, `agent_transcript.py`,
    `check_comment_audit.py`, `session_context.py`, `context_pack.py`,
    `stack_plan.py`) and add only the missing gates around them.

### G5 Abuse / failure
- Q: What breaks an operator's trust?
  - A: A gate that passes on missing evidence, or a runner that merges out of
    order. Both get explicit failure tests.

### G6 Verify
- Q: How will we know it works?
  - A: Unit tests per script, DAG and stack-plan checks on the epic's own
    tickets, and the full validation pack.

### G7 Priority
- Q: Why now?
  - A: The v1.4.57 ship closed the first fifteen items and left a coherent,
    mostly independent remainder; finishing it keeps the harness at one version.

## Clarifications

### 2026-11-27
- Q: Do the workflow-harness items belong in this ship?
  - A: Yes, as a separate PR from a clean worktree; the local checkout belongs to
    another session.
- Q: Should auto-merge be on by default?
  - A: No. `--auto-merge` is opt-in and the default path stops after each merge
    for the operator to confirm.

## Further Notes

The scorecard's per-item statuses were re-checked against `origin/main` at
`6f962df`; items 1, 4, 11, 12, 15, 20, 33, 35, 36, 37, 40, 41, 42, 45, 47 are
already wired.

## Handoff

- Next: `/execute_dev` (tickets 01–19 in layer order)
- Then: `/code_review` → `/cross_review` → `/behavior_validator` → `/pr_review --validate` → `/release_mgmt` → `/sync_docs`
