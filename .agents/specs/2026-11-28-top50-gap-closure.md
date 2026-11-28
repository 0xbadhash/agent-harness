# Close the remaining top-50 gaps

- **Product:** agent-harness
- **Created:** 2026-11-28
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** `.agents/BACKLOG.md`
- **Plan:** `.agents/specs/2026-11-28-top50-gap-closure-plan.md`
- **Tickets:** `.agents/specs/2026-11-28-top50-gap-closure/tickets`
- **Tracker:** local
- **Constitution:** AGENTS.md
- **Grill-me:** complete
- **Door:** two-way
- **Surface:** internal
- **Feature flag:** not-applicable (internal checks and docs; no user-visible surface)
- **Prototype:** none
- **Prototype verdict:** not-applicable (no shape question)
- **Reserved decisions:** release version numbers; whether the constraint check
  becomes a hard gate for every repo; installing skills into product trees.
- **Delegated decisions:** file names, CLI flag names, gate ids, glossary
  entries, and report paths.

## Problem Statement

The 2026-11-28 re-score left six partial items and three missing items in
agent-harness, plus one partial item in workflow-harness. Each gap is a
mechanism that exists but cannot fire, or a rule that exists in prose only:

1. There is no glossary artifact, so the domain-term and collision checks return
   `N/A` and `check_compact_safety.py` fails on the harness itself.
2. The comment audit classifies history, dead code, and TODO only. It has no
   route to an ADR, a test name, or a rewrite.
3. The ticket template omits `Kind`, `Prefactor`, `Touches`, and `Session`, so
   the prefactor gate has nothing to read and a ticket run records its session
   only in `TICKET_RUNS.jsonl`.
4. `merge_stack.py` merges in the foreground; a long stack holds the terminal.
5. `/execute_dev` and the plan template do not say that prototype code is a
   reference to reimplement.
6. workflow-harness has a retro module and tests, but nothing runs it on a
   schedule.

## Solution

Add the missing artifact and the missing inputs, then wire each check to a
deterministic command with a test. The glossary becomes `docs/glossary.md` and
both existing checks accept it. The comment audit gains a classification mode
and a constraint-to-test rule used by a new `/comment_audit` skill. The ticket
template gains the four fields; the runner writes the session id back to the
ticket. `merge_stack.py` gains a detached `--background` mode with a log. The
prototype contract gains a `**Prototype use:** reference` field and an import
check. workflow-harness gains a weekly retro workflow and a runner that writes
`docs/retros/`.

## Acceptance criteria

- [x] AC-1: `docs/glossary.md` exists with term → definition → owning surface
      rows; `scripts/check_glossary.py --root .` exits 0 and fails a duplicate
      normalized term; `spec_gate` and `check_compact_safety` accept the path.
- [x] AC-2: `check_comment_audit.py --classify` returns one of delete /
      move-to-ADR / move-to-test-name / rewrite per finding, and
      `skills/comment_audit/SKILL.md` documents the table and approval step.
- [x] AC-3: a comment that states a constraint and names no test, check, or
      `waive:` reason fails `--constraints`; a named test or waiver passes.
- [x] AC-4: the ticket template carries `Kind`, `Prefactor`, `Touches`, and
      `Session`; `check_ticket_dag` reads them; a shared-component ticket
      without a prefactor still fails.
- [x] AC-5: `run_tickets.py` writes `**Session:** <id>` to the ticket after a
      successful run with a session id; dry runs do not modify the ticket.
- [x] AC-6: `merge_stack.py --background` detaches, writes a log path, and
      prints the pid; `--dry-run` is unchanged.
- [x] AC-7: a named prototype requires `**Prototype use:** reference` in the
      spec or PR draft; source that imports `prototypes` fails the fidelity
      check.
- [x] AC-8: workflow-harness has a weekly scheduled workflow and
      `tools/weekly_retro.py`, which writes `docs/retros/<date>-<workflow>.md`
      from run records and exits 0 when none exist.
- [ ] Product smoke, full suite, hard gates, and `validate.py full` pass; no
      secrets are committed.

## Out of Scope

- Installing the updated skills into product trees (needs per-product approval).
- Closing or reopening GitHub pull requests.
- Making `--constraints` a hard gate for every repo in this ship.
- Changing the release policy or branch protection.

## Grill-me

**Status:** complete
**Date:** 2026-11-28

- Q: Should the glossary live at the repo root or under `docs/`?
  A: `docs/glossary.md`. The re-score named it, and the root already holds the
  product-facing files.
- Q: Should the constraint-to-test rule fail hard gates now?
  A: No. It ships as `--constraints` and the `/comment_audit` skill. Existing
  source has many constraint comments with no test, so a hard gate would fail
  unrelated work; the operator can promote it later.
- Q: Should `--background` use a daemon or a detached process?
  A: A detached process with a log and a pid. A daemon adds a supervisor and a
  second state model for one merge command.
- Q: Should the weekly retro run on a hosted runner with no run records?
  A: Yes, with a stated no-records result. The schedule is useful on a host with
  state, and the manual dispatch path stays available; inventing records would
  be worse.

## Further Notes

- `check_ticket_dag.py` already validates `Kind: shared-component` and
  `Prefactor:`; this ship makes the template emit those fields.
- `check_prototype_fidelity.py` already fails source that contains the prototype
  header or `DO NOT SHIP`; this ship adds the import route and the reference
  field.
- The re-score report names the same gaps in its "Open gaps" table.
