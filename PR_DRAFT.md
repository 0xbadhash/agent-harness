# PR Draft: Top-50 gap closure

**Range:** `origin/main...HEAD`

**Spec:** `.agents/specs/2026-11-28-top50-gap-closure.md`
**Plan:** `.agents/specs/2026-11-28-top50-gap-closure-plan.md`
**Tickets:** `.agents/specs/2026-11-28-top50-gap-closure/tickets`

## What Problem This Solves

The top-50 review left nine gaps. Six sat in this repo: no glossary the checks
could read, a comment audit with no dispositions and no constraint rule, a ticket
template that omitted Kind/Prefactor/Touches/Session, a DAG parser that misread
`None — can start immediately`, a foreground-only merge stack, and a prototype
contract with no reference declaration or import check. The ninth was a retro
module in workflow-harness that nothing scheduled.

## Why This Change Was Made

Each gap had a deterministic fix. One glossary file plus a standalone checker
gives the domain-term, collision, and compact-safety checks a single source.
Comment routes turn an audit finding into one of four actions. Ticket metadata
makes the DAG and the runner read the same fields the template writes. A
detached merge keeps a long stack off the terminal. A `**Prototype use:**`
field and an import check keep the sketch on the sketch side. A weekly workflow
runs the existing retro without inventing records.

## User Impact

- `/spec` now emits tickets with Kind, Prefactor, Touches, and Session, and the
  DAG gate reads them.
- `/execute_dev` writes the session id back to the ticket after a real run.
- `/comment_audit --classify` names a disposition per finding, and `--constraints`
  enforces the test-name or waiver rule.
- A long stack can merge with `--background`; the foreground default is unchanged.
- A named prototype must say `**Prototype use:** reference`; source that imports
  `prototypes` fails.
- workflow-harness gets a Monday retro schedule and `tools/weekly_retro.py`.

## Merge Danger

**Door:** two-way
**Blast Radius:** Harness gates, skill docs, and one new workflow file. Reverting
the commits restores the prior behavior; no product tree is installed.
**Surface:** internal
**Feature flag:** not-applicable (developer tooling, no runtime path)
**Prototype:** none
**Prototype verdict:** not-applicable
**Prototype use:** not-applicable

**Rollback:** revert the squash commits. `docs/glossary.md`, the new checks, and
the retro workflow are additive.

## Threat notes

**Tags:** supply-chain, secrets

- **Assets:** `.github/workflows/retro-weekly.yml` runs on a hosted runner with
  `contents: write` to commit generated reports. It runs a first-party script
  and installs only PyYAML.
- **Abuse cases:** the retro reads `var/state/*/run.jsonl` as data and never
  executes it; the script writes only under `docs/retros/`.
- **Supply chain:** no new runtime package. Tests import only the standard
  library plus existing pytest/PyYAML.

## Evidence

TDD: each ticket added a failing test first, then the implementation.

```text
red_cmd: git cat-file -e origin/main:scripts/check_glossary.py
green_cmd: python3 -m pytest -q
```

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | `python3 scripts/hard_gates.py --diff origin/main...HEAD` → ok |
| smoke | `python3 scripts/product_smoke.py --root .` → 2/2 |
| pytest | 665 passed, 2 skipped, 11 subtests |
| validate | `python3 scripts/validate.py full` → 9/9 |
| workflow-harness | 229 passed |

## Spec

**Spec:** `.agents/specs/2026-11-28-top50-gap-closure.md`

## Traceability

| AC | Test / check |
|----|----------------|
| AC-1 | `tests/test_glossary.py`, `scripts/check_glossary.py --root .` |
| AC-2 | `tests/test_comment_audit.py::TestCommentRoutes` |
| AC-3 | `tests/test_comment_audit.py::TestConstraintCheck` |
| AC-4 | `tests/test_ticket_metadata.py`, `check_ticket_dag.py` |
| AC-5 | `tests/test_ticket_metadata.py::test_real_run_writes_session` |
| AC-6 | `tests/test_stack_runners.py::test_background_argv_drops_only_the_flag` |
| AC-7 | `tests/test_prototype_and_handoff.py::test_source_importing_prototypes_fails` |
| AC-8 | `workflow-harness tests/test_weekly_retro.py` |

## Red-proof

```text
red_cmd: git cat-file -e origin/main:scripts/check_glossary.py
green_cmd: python3 -m pytest -q
repro_cmd: python3 scripts/check_ticket_dag.py .agents/specs/2026-11-28-top50-gap-closure/tickets
```

## Cross-review

See `.agents/artifacts/CROSS_REVIEW.md` (marker **CROSS-REVIEW**).

## Test plan

- [x] `python3 -m pytest -q`
- [x] `python3 scripts/spec_gate.py --root .`
- [x] `python3 scripts/check_ticket_dag.py .agents/specs/2026-11-28-top50-gap-closure/tickets`
- [x] `python3 scripts/check_compact_safety.py --root .`
- [x] `python3 scripts/hard_gates.py --diff origin/main...HEAD`
- [x] `python3 scripts/validate.py full`
- [x] workflow-harness `python3 -m pytest tests -q --ignore=tests/enhancement_specs`

## Things that look bad but are actually fine

1. `--constraints` fails on 110 existing comments in a whole-tree run. It is
   opt-in and meant for a ship diff; promoting it to hard gates would fail
   unrelated work, which the spec records as out of scope.
2. `--background` returns before the merge finishes. The printed pid and log
   path are the contract; the default foreground path still stops on a red
   check.
3. `_spawn_background` opens the log and passes the handle to `Popen`, then
   closes it in the parent. The child keeps its own descriptor, so the log keeps
   receiving output.
4. The weekly retro commits on a hosted runner that has no `var/state`. The
   guarded step commits only when a report exists and otherwise prints the
   no-records result.
5. `route_comment` returns `None` for a clean comment. Routes apply to audit
   findings, so a clean comment has nothing to migrate.
