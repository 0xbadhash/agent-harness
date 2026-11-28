# Plan — close the remaining top-50 gaps

**Spec:** `.agents/specs/2026-11-28-top50-gap-closure.md`
**Goal:** make every gap fire through a deterministic command, with tests.

## Approach

Each gap is closed by adding the missing input and then wiring the existing
check to it. No new service, no daemon, and no network call. The glossary and
ticket fields are data the checks already understand; the comment audit, merge
stack, and prototype check gain one mode or one field each. The workflow retro
gains a scheduled entry point around the existing `framework/retro.py`.

## Architecture

### 1. Glossary artifact and gate

- New `docs/glossary.md` with a table: term, definition, owning surface.
- `spec_gate.GLOSSARY_PATHS` and `check_compact_safety.GLOSSARY_PATHS` add
  `docs/glossary.md`.
- New `scripts/check_glossary.py` wraps `_glossary_entries` and
  `check_glossary_collisions`; it exits 0 with no file (skip), 0 on a clean
  table, and 1 on a collision or a row with no definition.
- Register `glossary` in `hard_gates.py`; skip on repos without a file.

### 2. Comment audit classification and constraint rule

- `classify_comment` keeps its finding kinds and gains a `route` function:
  - `delete` — history, commented code, ownerless TODO.
  - `move_to_adr` — the comment cites a decision, tradeoff, or supersession.
  - `move_to_test_name` — the comment states a constraint or race.
  - `rewrite` — an escape hatch that names no bound check.
- `--classify` prints `path:line  kind  route  text`.
- `--constraints` fails a constraint comment with no `test_…` name, no
  `scripts/…`/`tests/…` reference, and no `waive: <reason>`. It is opt-in.
- New `skills/comment_audit/SKILL.md` documents the table, the approval step,
  and the migration to test names; `docs/tdd.md` gains the same rule.

### 3. Ticket fields and session recording

- `skills/spec/references/spec-template.md` ticket block gains
  `**Kind:**`, `**Prefactor:**`, `**Touches:**`, and `**Session:**`.
- `check_ticket_dag` already reads Kind and Prefactor; add a `Touches` parse and
  keep the shared-component failure.
- `run_tickets.py` adds `record_session(ticket, session)`: replace an existing
  `**Session:**` line or append one after `**Status:**`. Dry runs skip it.

### 4. Background merge stack

- `merge_stack.py` gains `--background` and `--log PATH`.
- Background re-execs the same argv without `--background`, using
  `start_new_session=True`, `stdout=log`, `stderr=STDOUT`; it prints
  `background: pid=<pid> log=<path>` and exits 0.
- A `_background_argv` helper is unit-tested without spawning.

### 5. Prototype reference rule

- `templates/PR_DRAFT.md` and `skills/spec/references/spec-template.md` gain
  `**Prototype use:** reference`.
- `check_prototype_fidelity.py` requires the field when a prototype is named,
  and fails source that imports `prototypes` or `.agents/prototypes`.
- `skills/execute_dev/SKILL.md` and `plan-template.md` state the rule.

### 6. workflow-harness weekly retro

- New `tools/weekly_retro.py`: discover `var/state/*/run.jsonl`, run
  `framework.retro`, and write `docs/retros/<date>-<workflow>.md`; exit 0 with
  `no run records` when none exist.
- New `.github/workflows/retro-weekly.yml` with a weekly cron and
  `workflow_dispatch`; it runs the tool and the unit tests.
- Test the tool with a temporary run record.

## Data model

| Glossary term | Entity / field | Owner |
|---------------|----------------|-------|
| Glossary term | `term`, `definition`, `owner` | `docs/glossary.md` |
| Comment finding | `path`, `line`, `kind`, `route` | `check_comment_audit.py` |
| Ticket | `kind`, `prefactor`, `touches`, `session` | ticket file |
| Merge run | `pid`, `log`, `order` | `merge_stack.py` |
| Prototype use | `reference` | spec / PR draft |
| Retro report | `date`, `workflow`, `ranked improvements` | `docs/retros/` |

**Deletion policy:** a glossary term is deleted only after no spec, plan, or
ticket names it; the collision gate fails a duplicate, so remove the referencing
text first. A comment route is deleted only with its test. A scheduled retro is
removed by deleting the workflow and `tools/weekly_retro.py` together.

## Implementation sequence

1. Glossary artifact, standalone gate, and registration (AC-1, AC-4 data).
2. Comment audit routes, constraint mode, skill, and docs (AC-2, AC-3).
3. Ticket template fields and session write-back (AC-4, AC-5).
4. Background merge mode (AC-6).
5. Prototype reference field and import check (AC-7).
6. workflow-harness weekly retro (AC-8).
7. Release both repos and sync docs.

## Risks / mitigations

- A glossary table with a missing definition could fail existing specs. The
  checker requires a definition column; the new file supplies one for every row.
- `--constraints` could be noisy. It ships opt-in and the skill names the waiver
  form; the hard gate is unchanged.
- Detached merge has no supervisor. The log is the status surface, and the pid
  is printed; a failed merge leaves the log for the operator.
- A scheduled retro with no records writes nothing. It prints a no-records line
  so the job is not mistaken for a failure.

## Rollback

Revert the squash commit for each repo. The glossary and skill are additive;
removing the workflow file stops the schedule. No product behavior changes.
