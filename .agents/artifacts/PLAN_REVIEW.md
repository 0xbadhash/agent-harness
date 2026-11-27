# Plan review — harness wiring, spec rituals, stacked ships

**Marker:** PLAN-REVIEW
**Date:** 2026-11-27
**Plan:** `.agents/specs/2026-11-27-harness-wiring-stack-issues-plan.md`
**Reviewer:** implementer (pre-code pass)

## Verdict

APPROVE. The plan keeps the five helpers' contracts unchanged, wires them at
their natural stages, and keeps all issue creation offline by default. The
dependency order is buildable: tickets 01 and 02 are roots, 03 depends on the
glossary schema from 02, and 04/05 depend on the wiring from 01.

## Findings

1. The stack planner reuses `check_ticket_dag.load_tickets`, avoiding a second
   parser and keeping cycle semantics identical. No blocker.
2. `--gh` is a network path; the plan requires `--file-issues` first and an argv
   list. No blocker.
3. Cross-repo data (ticket 03) ships in `workflow-harness` with its own tests;
   the harness ship references it without editing the product tree. No blocker.
4. CI ticket DAG steps iterate existing directories, so repositories without
   specs tickets stay green. No blocker.

## Required before implementation

- Tests must be written first and must fail for the intended reason.
- Each changed script must be referenced from a test file (path-test gate).
- New comments must describe constraints; the comment audit runs on this diff.
