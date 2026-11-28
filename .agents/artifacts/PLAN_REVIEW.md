# PLAN-REVIEW — runner-label gate and follow-ups

**Marker:** PLAN-REVIEW
**Plan:** `.agents/specs/2026-11-28-runner-label-gate-plan.md`

## Coverage

- AC-1 and AC-2 map to `check_workflow_runners.check()` and the five fixture
  tests. The skip paths (no workflows, no allowlist) are explicit, so the gate
  cannot fail an unrelated product on first install.
- AC-3 maps to the `hard_gates.py` registration. The gate is scoped to the
  workflow and allowlist paths in the diff; a full-tree run still checks because
  the findings are cheap.
- AC-4 maps to the workflow-harness workflow edit and its local test. The
  permissions block and `GITHUB_TOKEN` are asserted, because those are the two
  things a hosted-runner move could break.
- AC-5 and AC-6 are reports. The plan pins the commits and fixes the verdict
  vocabulary, which is the weakness the challenge named in the first scorecard.

## Risks

- The allowlist is a declaration, not a registry read. A repo can declare a label
  it does not have. The gate message states this limit, and the check still
  catches the common case: a label copied from another repo.
- `runs-on` expressions are skipped as unresolved. A matrix expression that
  resolves to an undeclared label would pass. Resolving expressions statically
  is out of scope; the plan says so.
- The reports are a point-in-time audit. Pinned commits make them reproducible
  and stale by design.

## Findings

- P1: none.
- P2: the gate adds PyYAML as an import in a script that `hard_gates.py` calls
  in-process. PyYAML is already a test dependency and is installed in CI, but a
  product that vendors the script without PyYAML would fail at import. The
  implementation imports yaml lazily inside `check()` and returns a finding that
  says the dependency is missing, rather than crashing the whole gate run.

**Verdict:** approve.
