# PR Draft: Runner-label gate, workflow-harness fix, re-score and PR triage

**Range:** `origin/main...HEAD`

**Spec:** `.agents/specs/2026-11-28-runner-label-gate.md`
**Plan:** `.agents/specs/2026-11-28-runner-label-gate-plan.md`
**Tickets:** `.agents/specs/2026-11-28-runner-label-gate/tickets`

## What Problem This Solves

workflow-harness defined both review-tier jobs with `runs-on: self-hosted`. No
self-hosted runner is attached, so the auto-merge job queued forever on the last
two PRs and merged anyway because the check is not required. The harness had no
way to catch a runner label that no machine provides. Separately, the v1.5.0
release claim about the top-50 items had not been checked against the shipped
commits, and four open PRs predate that ship.

## Why This Change Was Made

The queued job is a dead gate: amber on every PR, ignored by everyone. The cause
is a declared runner label with no runner, which is a class of mistake a small
deterministic check can catch. The re-score and triage are read-only proof, so
the completion claim and the PR backlog stop living in a chat summary.

## User Impact

- A PR that names an undeclared runner label fails at PR time with the workflow,
  job, and label named.
- workflow-harness review-tier jobs complete on a hosted runner instead of
  queueing.
- The top-50 scorecard has a dated re-score against pinned commits, with the
  runnable check and exit code recorded per item.
- The four open PRs get a supersession verdict and a close/revive recommendation.

## Merge Danger

**Door:** two-way
**Blast Radius:** Harness-wide gate registration and one workflow file. Reverting
the commit removes the gate and restores the workflow; repos without an allowlist
are skipped, so no existing product changes behavior.

**Rollback:** revert the squash commits for agent-harness and workflow-harness
together. The reports under `/srv/boxdrop/out/` are additive.

## Threat notes

**Tags:** secrets, supply-chain

- **Assets:** `.github/workflows/*.yml` and `.github/allowed-runners.txt` in the
  checked tree; both are read as data and never executed.
- **Abuse cases:** a workflow that names an undeclared runner is reported, not
  silently accepted; a `runs-on` expression is reported as unresolved so a
  crafted expression cannot smuggle a label past the gate.
- **Supply chain:** no new package is added; the checker imports PyYAML, which
  the test environment and CI already install.

`check_workflow_runners.py` reads workflow YAML and a text allowlist only. It
runs no shell command from the files it reads, makes no network call, and writes
nothing. The workflow-harness change keeps `secrets.GITHUB_TOKEN` and the
existing `permissions:` block; no custom secret is introduced.

## Things that look bad but are actually fine

1. A repo with workflows but no `.github/allowed-runners.txt` is skipped, so the
   gate does not fire there. This is deliberate opt-in: the allowlist is the
   repo's statement of which runners exist, and docs/ci-matrix.md states it.
2. `runs-on: ${{ ... }}` is reported as `unresolved` and does not fail. A matrix
   expression can expand to a declared label, so treating the raw text as a
   finding would produce false positives.
3. The `except ImportError` around the checker registration looks like a
   swallowed failure. It covers a partial install where the module is absent and
   appends a hard-gate violation with the error text.
4. The reports under `/srv/boxdrop/out/` are outside the repo and carry no tests.
   They are read-only evidence with a recorded command and exit code per row.

## Traceability

- AC-1 → `tests/test_workflow_runners.py::test_declared_label_passes` and
  `::test_undeclared_label_fails_with_names`
- AC-2 → `::test_no_workflows_skips`, `::test_no_allowlist_skips`,
  `::test_empty_allowlist_fails`
- AC-3 → `::test_hard_gate_runs_on_workflow_diff` and
  `::test_hard_gate_skips_unrelated_diff`
- AC-4 → workflow-harness `tests/test_workflow_runners.py`
- AC-5 → `/srv/boxdrop/out/SCORECARD-GROKBUILD-HARNESS-TOP50-RESCORE-2026-11-28.md`
- AC-6 → `/srv/boxdrop/out/TRIAGE-PRS-2026-11-28.md`

## Evidence pack

- hard_gates: `python3 scripts/hard_gates.py --diff origin/main...HEAD` → pass
- pytest: `python3 -m pytest -q` → 596+ passed, 3 skipped
- validate: `python3 scripts/validate.py full` → 9/9 gates
- smoke: `python3 scripts/product_smoke.py --root .` → 2/2 steps
- workflow-harness: `python3 -m pytest tests -q --ignore=tests/enhancement_specs`
  → 219 passed

## Red-proof

```text
red_cmd: git cat-file -e origin/main:scripts/check_workflow_runners.py
green_cmd: python3 -m pytest tests/test_workflow_runners.py -q
```

The red command exits 128 because the gate does not exist on the base commit;
the green command covers the new checker.
