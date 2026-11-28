# Plan — runner-label gate and post-release follow-ups

**Spec:** `.agents/specs/2026-11-28-runner-label-gate.md`
**Goal:** one portable gate, one workflow fix, two read-only reports.

## Data model

| Term | Fields | Source |
|------|--------|--------|
| Runner label | `name`, `declared_at`, `used_by` | `.github/allowed-runners.txt` + workflow YAML |
| Workflow job | `workflow`, `job`, `runs_on` | `.github/workflows/*.yml` |
| Gate finding | `workflow`, `job`, `label`, `message` | `check_workflow_runners.check()` |
| Scorecard row | `id`, `title`, `verdict`, `evidence`, `delta` | re-score report |

**Deletion policy:** remove a label from the allowlist only after no workflow
names it; the gate fails on a used-but-undeclared label, so the deletion order is
workflow first, allowlist second. The script itself is deleted only with its
tests and its `hard_gates.py` registration in the same change.

## Shape

### 1. Harness script (`scripts/check_workflow_runners.py`)

```text
parse .github/workflows/*.yml   -> [(workflow, job, label)]
read .github/allowed-runners.txt -> set[str]
findings = used - declared
exit 0: no findings (or no workflows / no allowlist, with a stated skip)
exit 1: one line per finding, "workflow:job uses runner <label> (not declared)"
```

- YAML via PyYAML (already a test dependency; CI installs it).
- `runs-on` may be a string or a list; list entries are each checked.
- `runs-on` may be an expression (`${{ ... }}`); expressions are reported as
  `unresolved` and do not fail, so a matrix expression is not a false positive.
- Reusable workflows (`jobs.<id>.uses`) have no `runs-on`; skip.

### 2. Gate registration (`scripts/hard_gates.py`)

- Gate id `workflow_runners`.
- Runs when the diff names `.github/workflows/` or
  `.github/allowed-runners.txt`, or when the repo has both and the diff is a
  full-tree check.
- Skipped with a reason otherwise. A finding is a hard failure.

### 3. Tests (`tests/test_workflow_runners.py`)

- Temporary repo, declared label passes.
- Undeclared label fails and the message names workflow, job, label.
- No workflows → skip ok; no allowlist → skip ok; empty allowlist + a label →
  fail.
- List-valued `runs-on` checks every entry; expression → unresolved, no fail.

### 4. workflow-harness companion

- Both `review-tiers.yml` jobs → `ubuntu-latest`.
- `.github/allowed-runners.txt` with `ubuntu-latest`.
- `tests/test_workflow_runners.py` asserting the same contract against that
  repo's workflows and allowlist.
- `ci.yml` step "Runner labels are declared".

### 5. Reports (read-only)

- `/srv/boxdrop/out/SCORECARD-GROKBUILD-HARNESS-TOP50-RESCORE-2026-11-28.md`
  with pinned commits `f1547d3` / `58f5a56`, a per-item verdict table, the
  runnable check and exit code where one exists, and a delta column.
- `/srv/boxdrop/out/TRIAGE-PRS-2026-11-28.md` with per-PR supersession evidence
  and a close/revive recommendation.

## Order

1. Script + tests (TDD: failing test first).
2. Gate registration + docs.
3. workflow-harness companion + its test.
4. Reports.
5. Release: agent-harness v1.5.2, workflow-harness v0.3.3.

## Risks / rollback

- PyYAML is already used by the workflow-harness tests and CI installs it; the
  harness tests already import yaml elsewhere, so no new dependency.
- A product with workflows but no allowlist is skipped, not failed, until it
  adopts the file. Docs state the opt-in.
- Rollback: revert the harness commit and the workflow change together; the gate
  is additive and skips on repos without the allowlist.
