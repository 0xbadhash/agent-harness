# Wire orphaned harness helpers, tighten spec rituals, and plan stacked ships

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** `.agents/BACKLOG.md` → Open work
- **Plan:** `.agents/specs/2026-11-27-harness-wiring-stack-issues-plan.md`
- **Tickets:** `.agents/specs/2026-11-27-harness-wiring-stack-issues/tickets`
- **Tracker:** local
- **Constitution:** `AGENTS.md` + `.agents/policy/base_constraints.md`
- **Grill-me:** complete

## Problem Statement

Five deterministic helpers already exist in `agent-harness` but no skill, CI job, or
gate calls them: `retro_job.py`, `smart_zone_guard.py`, `check_compact_safety.py`,
`check_comment_audit.py`, and `check_ticket_dag.py`. Operators therefore get no
runtime benefit from the work that produced them, and the same gaps recur: retros
stay prose, implementer context overruns the smart zone, compaction runs before the
spec is on disk, comments accumulate history instead of constraints, and ticket
graphs are never validated.

The spec ritual also stops short of the decisions that make names and priorities
stick: it has no candidate-name scenario table, no operator stop token, no
why-first question order, no pain ranking, and no glossary collision check.
`workflow-harness` references a `glossary.json` that does not exist and its
`tickets/02-ingest-fanout.md` lacks acceptance criteria and a blocking edge.
Review and QA artifacts do not produce issues, so clusters of findings are lost.
Large ships have no stack manifest and no per-layer review chunks.

## Solution

Wire the five helpers into the skills and CI that own their stage; make the spec
ritual ask why first, rank pain, offer a stop token, and prove candidate names
against scenarios; fail the spec gate on colliding glossary terms; add the
missing `workflow-harness` glossary and ticket fields; teach the retro and QA
flows to write issue bodies (and only call `gh` on explicit opt-in); and add a
stack planner that emits ordered layers for implementation and review chunking.

## User Stories

1. As a harness operator, I want `/execute_dev` to validate the ticket DAG and
   block compaction past the smart zone, so a long build does not lose decisions.
2. As a reviewer, I want `/code_review` to run the comment audit and review a
   stacked diff layer by layer, so findings stay local and actionable.
3. As a spec writer, I want the grill to ask why before what and to rank pain, so
   we build the smallest valuable slice.
4. As a maintainer, I want `workflow-harness` domain terms and tickets to carry
   definitions, acceptance criteria, and blocking edges, so the DAG is real.
5. As a release owner, I want retro/QA clusters to become issue bodies and an
   umbrella issue, so follow-ups survive the session.

## Implementation Decisions

- Skills invoke existing scripts; the helper scripts keep their current CLI and
  semantics.
- Issue creation is offline by default. `--file-issues` writes Markdown bodies
  under `.agents/artifacts/issues/`; `--gh` is the only network path and is
  opt-in.
- The stack planner is deterministic: it reads ticket `Blocked by:` edges and
  emits topological layers with a per-layer estimate and review chunk list.
- CI adds the comment audit on the pull-request diff and validates every
  `.agents/specs/*/tickets` directory.
- `workflow-harness` stays a separate tree; its data and tests ship in that repo.

## Testing Decisions

- External behavior only: CLI exit codes, written artifacts, and skill text
  contracts.
- Seams: `scripts/retro_job.py`, `scripts/stack_plan.py`, `scripts/spec_gate.py`,
  and the workflow-harness JSON/ticket files.
- Commands: `pytest tests/test_harness_wiring_stack.py`,
  `python3 scripts/product_smoke.py --root .`, and the workflow-harness suite.
- TDD applies: new tests are written before implementation.

## Acceptance Criteria

- [ ] **AC-1:** `retro_job`, `smart_zone_guard`, `check_compact_safety`,
  `check_comment_audit`, and `check_ticket_dag` are invoked from the owning
  skills, and CI runs the comment audit and ticket DAG checks.
- [ ] **AC-2:** The spec ritual documents a candidate-name scenario table, an
  operator stop token, why-first question order, and pain ranking; `spec_gate.py`
  fails on glossary term collisions.
- [ ] **AC-3:** `workflow-harness/glossary.json` defines the ingest terms, and
  `tickets/02-ingest-fanout.md` carries `**Blocked by:**`, `**Status:**`, and at
  least three checkable acceptance boxes.
- [ ] **AC-4:** `retro_job.py --file-issues` writes one issue body per cluster
  plus an umbrella issue, `qa_campaign` documents the flow, and no `gh` call runs
  without `--gh`.
- [ ] **AC-5:** `scripts/stack_plan.py` emits ordered layers and review chunks
  from ticket blocking edges; `/execute_dev` and `/code_review` reference it.
- [ ] Product smoke commands succeed.
- [ ] No secrets committed.

## Out of Scope

- Creating real GitHub issues during this ship; only local issue bodies.
- Changing product trees or the five helper CLIs beyond additive flags.
- A new runtime, database, or scheduler.
- Replacing the existing review personas or validators.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: What does "done" look like in one sentence an operator would say?
  - A: Every new helper is reachable from the stage that needs it, and each gate
    fails closed with a command the operator can rerun.

### G2 Non-goal / kill
- Q: What must we not build, and what would cancel this?
  - A: No automatic GitHub issue creation, no product-tree edits, and no new
    runtime. Cancel if wiring would require rewriting a helper's contract.

### G3 Wrong product
- Q: Is this the right repo and surface?
  - A: Yes. Four items are harness skills/scripts; item three is the
    `workflow-harness` data companion.

### G4 Cheapest alternative
- Q: What is the smallest ship that still proves value?
  - A: Skill and CI invocations plus two small scripts. The helpers already exist.

### G5 Abuse / failure
- Q: How can this be misused or fail?
  - A: Ticket and glossary parsers must treat file content as untrusted. Issue
    bodies could be injected with shell text; `--gh` stays opt-in and uses argv
    lists, with secrets scanned before any post.

### G6 Verify
- Q: How do we prove it before merge?
  - A: New pytest cases for each AC, CLI runs of the wired helpers, harness
    smoke, and the workflow-harness suite.

### G7 Priority / delay
- Q: Why now, and what happens if we ship nothing?
  - A: These are already-built gates losing value. Delay keeps the same review,
    compaction, and naming failures recurring.

### Pain ranking
1. Orphaned helpers (highest operator pain: gates exist but never run).
2. Spec ritual gaps (wrong names and unranked scope recur).
3. Stack planning and review chunking (large ships stall).
4. Issue-producing retro/QA (findings disappear).
5. `workflow-harness` data (blocks the glossary gate from being useful).

### Operator stop token
- Q: How does the operator stop a bad idea without filling the interview?
  - A: Reply `STOP`; the spec status becomes `rejected` and no tickets are written.

## Clarifications

### 2026-11-27
- Q: Should the ship open real GitHub issues?
  - A: No. Write issue bodies locally and keep `--gh` behind explicit operator
    approval.
- Q: Should `agent-harness` edit the `workflow-harness` tree in the same commit?
  - A: No. Ship its glossary and ticket data in the `workflow-harness` repo with
    its own tests.

## Further Notes

- The five helpers are deterministic and already covered by existing tests; this
  ship adds wiring tests, not a rewrite.
- Glossary collisions are compared after lowercasing and stripping non-alphanumerics,
  so `policy_id` and `Policy ID` collide while distinct terms do not.

## Handoff

- Next: `/execute_dev` (one sub-task per ticket; TDD)
- Then: `/code_review` → `/cross_review` → `/behavior_validator` →
  `/pr_review --validate` → `/release_mgmt` → `/sync_docs`
