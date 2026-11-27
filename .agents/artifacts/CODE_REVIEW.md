# Code review — T2088U harness wiring, spec rituals, issue flows, stack plan

**Marker:** CODE-REVIEW
**Command:** `/code_review` closeout pass
**Base:** `0336317`
**Head:** `HEAD` (3 commits)
**Scope:** 24 files, +1,063 / −75, non-test LOC 931, large diff

## Standards

Reviewed against the repo style (typed Python, deterministic scripts, no host
paths) and the Fowler smell baseline:

- `Mysterious Name` — none. `stack_plan`, `write_issue_bodies`, and
  `check_glossary_collisions` name their effect.
- `Duplicated Code` — the ticket DAG is parsed once; `stack_plan` imports
  `check_ticket_dag` instead of copying the parser.
- `Feature Envy` — `retro_job` owns issue bodies because it already owns the
  clusters.
- `Data Clumps` — the plan dict is a deliberate output shape consumed by the
  Markdown and JSON writers.
- `Primitive Obsession` — ticket ids stay strings because the on-disk format is
  numeric-prefixed Markdown.
- `Repeated Switches` — none.
- `Shotgun Surgery` — skill edits are one line per stage; no cross-cutting edit.
- `Divergent Change` — `spec_gate` gained one checker beside the existing ones.
- `Speculative Generality` — no unused flags; every new branch has a test.
- `Message Chains`, `Middle Man`, `Refused Bequest` — none.

Verdict: pass. No standing refactor required.

## Spec

AC-by-AC fidelity:

- AC-1: wired, `test_ac_1_helpers_wired` asserts the skill and CI commands.
- AC-2: wired, `test_ac_2_spec_rituals_and_glossary_collision` asserts the four
  rituals and both collision outcomes.
- AC-3: companion tree, `workflow-harness/tests/test_glossary_and_tickets.py`
  plus the harness companion test.
- AC-4: `test_ac_4_issue_bodies_offline` proves file output and no subprocess
  call; `--gh` without `--file-issues` returns 2.
- AC-5: `test_ac_5_stack_plan_layers_and_chunks` proves layers, chunks, write,
  cycle, and unknown-dependency failure.

Scope creep: the four base-repair pieces (diagnosing-bugs skill, review axes,
Merge Danger template, GLOSSARY references) restore tests that the base commit
already carried. Verdict: pass.

## Findings

1. **P1 — unknown ticket dependency was silently satisfied.** Accepted and
   fixed: `stack_plan` now raises `MissingDependency` and exits 1; the test
   covers the `**Blocked by:** 99` case.
2. **P1 — `--gh` can publish untrusted issue text.** Accepted as existing risk;
   mitigated by an argv list, an explicit flag, `--file-issues` as a
   prerequisite, and the secrets scan before release. No code change.
3. **P2 — default LOC estimate is 150.** Follow-up: read a real estimate when
   tickets add one. Not blocking.
4. **P2 — CI ticket DAG step scans `.agents/specs/*/tickets` only.** Follow-up:
   product repos with another ticket root need their own invocation. Documented.

P0 count: 0. Follow-ups: 2.

## Review chunks

- **CHUNK 1 (tickets 01, 02):** skills, CI, `spec_gate` collision. Verdict: pass.
- **CHUNK 2 (tickets 03, 04, 05):** workflow-harness data, `retro_job` issue
  bodies, `stack_plan`. Verdict: pass after the P1 dependency fix.

## Evidence

- Secrets: `check_secrets_diff.py --base origin/main --head HEAD` → clean.
- Comment audit: `check_comment_audit.py --diff origin/main...HEAD --strict` → clean.
- Tests: targeted 5/5; full suite 483 passed, 1 skipped.
- Smoke: `product_smoke.py` 2/2; `validate.py full` 6/6.
- Lint/type: ruff clean; mypy success on 216 files.

## Correction checks

- P1 unknown ticket dependency was rendered as `ready` → `tests/test_harness_wiring_stack.py::test_ac_5_stack_plan_layers_and_chunks` asserts exit 1 on a missing dependency.
- P1 `--gh` could post issue bodies without an explicit call → `tests/test_harness_wiring_stack.py::test_ac_4_issue_bodies_offline` asserts `--gh` alone exits 2 and the default path writes files only.
- P2 default LOC estimate of 150 → no-check: estimate text is evidence only and never gates a merge.
- P2 CI ticket DAG step scans `.agents/specs/*/tickets` only → no-check: product ticket roots belong to product CI and are documented in `execute_dev`.

## Handoff

✅ CODE-REVIEW DONE  p0=0  follow_ups=2
NEXT_SKILL=/cross_review
