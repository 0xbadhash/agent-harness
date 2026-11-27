# PR Draft: Wire orphaned harness helpers, tighten spec rituals, plan stacked ships

**Range:** `origin/main..HEAD`
**Spec:** `.agents/specs/2026-11-27-harness-wiring-stack-issues.md`
**Plan:** `.agents/specs/2026-11-27-harness-wiring-stack-issues-plan.md`
**Tickets:** `.agents/specs/2026-11-27-harness-wiring-stack-issues/tickets`

## Summary

- Wired `retro_job.py`, `smart_zone_guard.py`, `check_compact_safety.py`,
  `check_comment_audit.py`, and `check_ticket_dag.py` into their owning skills
  and CI jobs (AC-1).
- Added the candidate-name scenario table, operator `STOP` token, why-first
  question order, pain ranking, and a glossary collision gate (AC-2).
- Added `workflow-harness/glossary.json` and real ticket fields for the ingest
  fan-out (AC-3).
- Added offline issue-body generation to the retro job and documented the QA
  flow (AC-4).
- Added `scripts/stack_plan.py` for stack layers and per-layer review chunks
  (AC-5).

## What Problem This Solves

The harness had five deterministic helpers that no stage called. The ticket DAG
validator, smart-zone guard, compact-safety gate, comment audit, and retro job
therefore had no effect on a real ship. Spec interviews also missed the decisions
that prevent rework: why the work matters, which pain ranks first, whether a
candidate name survives real scenarios, and whether two glossary rows define the
same term. `workflow-harness` pointed at a `glossary.json` that did not exist,
and its ingest ticket had no acceptance criteria or blocking edge. Retro and QA
findings stayed in session artifacts. Large diffs had no layer plan or review
chunks.

## Why This Change Was Made

The helpers already encode the intended behavior, so the smallest useful change
is to invoke them at the stage that owns the risk. The planner reuses the ticket
DAG parser to avoid a second dependency model. Issue bodies are files first so
the default path stays offline and deterministic; `gh` is a thin, explicit
adapter. The spec edits are prose contracts with exact commands, which tests can
assert without adding a runtime.

## User Impact

Harness operators and agents get fail-closed checks where they already work:
`/execute_dev`, `/code_review`, `/retrospect`, `/qa_campaign`, and CI. Product
installs keep working because the helper CLIs are unchanged; only additive flags
and new commands appear. No user-visible product change.

## Smallest visual change

The smallest slice is one command in this repo:

```bash
python3 scripts/stack_plan.py --tickets .agents/specs/2026-11-27-harness-wiring-stack-issues/tickets
```

It prints the dependency layers and review chunks for the five ship tickets.
Every other item is the same pattern: one existing helper invoked from the skill
or CI step that owns the risk.

## Before/after

**Before:** the helper scripts existed, but no skill or CI job named them, so a
real ship never ran them. The base commit had no stack planner at all.

```text
$ git grep -l "check_ticket_dag" 0336317 -- skills .github || echo "no skill/CI caller"
no skill/CI caller
$ git cat-file -e 0336317:scripts/stack_plan.py; echo $?
128
```

**After:** each helper has a named caller, and the planner runs offline:

```text
$ python3 scripts/stack_plan.py --tickets .agents/specs/2026-11-27-harness-wiring-stack-issues/tickets
### CHUNK 1 — tickets 01, 02
### CHUNK 2 — tickets 03, 04, 05
$ .venv/bin/python -m pytest tests/test_harness_wiring_stack.py -q
5 passed in 0.07s
```

## Merge Danger

**Door:** two-way
**Blast Radius:** harness

## Evidence

New tests in `tests/test_harness_wiring_stack.py` failed before the
implementation and pass after it. The workflow-harness test file covers the
glossary and ticket fields in its own tree. The full harness suite (483 passed,
1 skipped), `validate.py full` (6/6), and product smoke (2/2) are green. This
ship also restores four pieces that the base commit tested but left
uncommitted: the diagnosing-bugs skill, the two review axes, the Merge Danger
template block, and the `GLOSSARY.md` references.

```text
red_cmd: git cat-file -e origin/main:tests/test_harness_wiring_stack.py
green_cmd: .venv/bin/python -m pytest tests/test_harness_wiring_stack.py -q
```

## Evidence pack

| Item | Result |
|------|--------|
| pytest | `tests/test_harness_wiring_stack.py` — 5 passed; full suite 483 passed, 1 skipped |
| smoke | `product_smoke.py` — 2/2 passed |
| validate | `validate.py full` — 6/6 gates passed |
| hard_gates | `hard_gates.py` — pass |

## Spec

**Spec:** `.agents/specs/2026-11-27-harness-wiring-stack-issues.md`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 | `tests/test_harness_wiring_stack.py::test_ac_1_helpers_wired` |
| AC-2 | `tests/test_harness_wiring_stack.py::test_ac_2_spec_rituals_and_glossary_collision` |
| AC-3 | `workflow-harness/tests/test_glossary_and_tickets.py` (companion tree) |
| AC-4 | `tests/test_harness_wiring_stack.py::test_ac_4_issue_bodies_offline` |
| AC-5 | `tests/test_harness_wiring_stack.py::test_ac_5_stack_plan_layers_and_chunks` |
| smoke | `product_smoke.py` (`hardcodes`, `unit`) |

## Threat notes

- **Path traversal:** ticket and glossary inputs are untrusted Markdown/JSON.
  Parsers keep strict token regexes and resolve paths under the repo root.
- **Injection:** issue bodies are written as files; `--gh` uses an argv list and
  never a shell string. Default execution makes no network call.
- **Secrets:** `check_secrets_diff.py` runs on the ship range before issue
  bodies are eligible for posting.

## Red-proof (process honesty)

The wiring tests do not exist on `origin/main` and failed on import/collection.
After implementation the same tests pass.

```text
red_cmd: git cat-file -e origin/main:tests/test_harness_wiring_stack.py
green_cmd: .venv/bin/python -m pytest tests/test_harness_wiring_stack.py -q
```

## Cross-review

See `.agents/artifacts/CROSS_REVIEW.md` (marker `CROSS-REVIEW`).

## Things that look bad but are actually fine

1. **Issue bodies are local files, not GitHub issues.** The ship is deterministic
   and offline; `--gh` remains an explicit operator action with its own approval.
2. **The stack planner reads ticket Markdown instead of a new manifest format.**
   Tickets already carry `Blocked by:` edges, so one parser keeps the DAG and the
   layers consistent.
3. **Skill edits are prose rather than Python gates.** The scripts stay the
   enforcement point; the skill text tells the agent which command to run, and
   tests assert the command appears.
4. **`workflow-harness` data ships in a companion repo.** Its glossary and ticket
   schema belong to that product's tests, so the harness ship references them
   without editing product code.
