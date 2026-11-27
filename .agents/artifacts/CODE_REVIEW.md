# CODE-REVIEW — automation readiness gate

**Marker:** CODE-REVIEW

- Command: `python3 scripts/next_skill.py --after execute_dev --base origin/main --head HEAD`
- Base: `origin/main` · Head: `HEAD`
- Secrets scan: covered by `hard_gates` (`check_secrets_diff.py`)

## Standards

- `check_automation_ready.py` follows the `(ok, messages)` contract used by the
  other scanners and returns failure rows that name the remedy.
- Checker imports happen inside `check` so a product without a sibling script
  gets an explicit `fail:` row instead of an import crash.
- `night_shift_autofix._readiness_block` converts a bad artifact into a single
  attempt record; the fixer set is unchanged.
- `night_shift_readiness.py` reads the flag from the plugin with env override and
  passes it through one call site.
- No P0 findings.

## Spec

- AC-1 is `tests/test_automation_ready.py::TestAutomationReadyCheck`.
- AC-2 is `tests/test_automation_ready.py::TestReadinessArtifact`.
- AC-3 is `tests/test_automation_ready.py::TestAutofixReadinessGate`.
- AC-4 is the `require_ready` resolution in `night_shift_readiness.py`.
- AC-5 is `.agents/product_plugin.yaml` plus `.agents/docs/night-shift.md`.
- AC-6 is the full suite, smoke, and validate run.
- Scope matches the spec; no unrelated style churn.

## Correction checks

- Automation could run on a broken inner loop → tests/test_automation_ready.py
- A stale artifact could authorize work → tests/test_automation_ready.py::TestReadinessArtifact
- A failed check could be recorded as ready → tests/test_automation_ready.py::TestReadinessArtifact
- An ownerless run could pass → tests/test_automation_ready.py::TestAutomationReadyCheck
- The fixer set could run despite refusal → tests/test_automation_ready.py::TestAutofixReadinessGate
- Flag wiring could regress → tests/test_night_refresh_from_orchestrator.py
- A missing checker could crash the gate → tests/test_automation_ready.py::TestAutomationReadyCheck::test_missing_checker_is_named

## Findings

- P0: none.
- Follow-ups: refresh the artifact from a green `validate.py full` once the nightly
  cadence is stable.

## Verdict

Approve. The targeted tests went red first, the full suite is green, mypy is
clean, and validate is 9/9.
