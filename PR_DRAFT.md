# PR Draft: Automation readiness gate before the outer loop

**Range:** `origin/main..HEAD`
**Owner:** 0xbadhash

## What Problem This Solves

The bounded outer loop runs mechanical fixers after a gate failure. It had no
proof that the inner loop itself was sound, so an expired suppression, an
unmapped correction, a stale behavior report, or an old coverage artifact could
start a repair run on a broken base. The fixers then added noise and masked the
real failure.

## Why This Change Was Made

Automation may only touch the tree when the inner loop is proven. The proof is a
timestamped artifact computed from the same checkers the PR gate uses, and the
outer loop reads that artifact before it changes anything.

## User Impact

- `check_automation_ready.py` fails closed on any of: lint ratchet, suppression
  ban, correction map, behavior report, fresh coverage, named owner.
- `--write` records `.agents/artifacts/AUTOMATION_READINESS.md`.
- `attempt_autofix(require_readiness=True)` returns one `autofix_blocked` record
  and runs no fixer without a current artifact.
- `night_shift_readiness.py` sets the flag from
  `night_shift.require_automation_ready` or `AUTOFIX_REQUIRE_READY=1`.
- Default is off for products; the harness opts in through its plugin.

## Evidence pack

| Gate | Command | Result |
|------|---------|--------|
| Red proof | `python3 -m pytest tests/test_automation_ready.py -q` | collection failed before `check_automation_ready.py` existed |
| Targeted tests | `python3 -m pytest tests/test_automation_ready.py -q` | 13 passed |
| Night-shift tests | `python3 -m pytest tests/test_night_refresh_from_orchestrator.py tests/test_night_shift_runtime_ops430.py tests/test_night_shift_todo_and_hardcodes.py -q` | 35 passed including the new file |
| Mypy | `python3 -m mypy scripts tests` | success, 222 files |
| Lint ratchet | `python3 scripts/check_lint_ratchet.py` | four rules held at baseline |
| Full suite | `python3 -m pytest -q` | 520 passed, 2 skipped |
| Smoke | `python3 scripts/product_smoke.py --root .` | 2/2 steps passed |
| Validate | `python3 scripts/validate.py full` | 9/9 gates passed |
| Readiness live run | `check_automation_ready.py --owner 0xbadhash --write` | all rows ok, artifact written |
| Hard gates | `python3 scripts/pr_validator.py --diff origin/main...HEAD` | score gate |

**Spec:** `.agents/specs/2026-11-27-automation-readiness-gate.md`
**Plan:** `.agents/specs/2026-11-27-automation-readiness-gate-plan.md`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 precondition failure is named | `tests/test_automation_ready.py::TestAutomationReadyCheck` |
| AC-2 artifact write/validate | `tests/test_automation_ready.py::TestReadinessArtifact` |
| AC-3 autofix refusal | `tests/test_automation_ready.py::TestAutofixReadinessGate::test_outer_loop_blocked_without_artifact` |
| AC-4 flag wiring | `tests/test_automation_ready.py::TestAutofixReadinessGate` plus `night_shift_readiness.py` |
| AC-5 plugin + docs | `.agents/product_plugin.yaml`, `.agents/docs/night-shift.md` |
| AC-6 suite/smoke/validate | full pytest 520 passed; smoke 2/2; validate 9/9 |

## Threat notes

Security tags: `supply-chain`, `secrets`.

- Asset / trust boundary: the gate reads repository artifacts and runs local
  checkers; it makes no network calls and reads no credentials.
- Abuse case: automation could reformat over a real gate failure — the readiness
  artifact forces the inner loop green first (`supply-chain` integrity).
- Abuse case: a stale artifact could authorize work on an old commit — the 24h
  cap and the failed-check scan reject it.
- Abuse case: an ownerless automation run has no accountability — the gate
  requires a named owner from `--owner`, `AUTOMATION_OWNER`, or `PR_DRAFT.md`.

## Red-proof (process honesty)

Red was observed before implementation: the targeted run failed collection with
`ModuleNotFoundError: No module named 'check_automation_ready'`, and
`attempt_autofix(require_readiness=True)` had no refusal path. The retained green
command is executable:

```text
green_cmd: python3 -m pytest tests/test_automation_ready.py tests/test_night_refresh_from_orchestrator.py -q
```

## Things that look bad but are actually fine

1. The harness opts in while products default off. Opt-in proves the gate on the
   reference repo; a product without coverage must not be blocked by default.
2. Coverage reads 47.8%. The gate checks freshness and presence, while
   `check_module_coverage.py` owns the threshold.
3. `AUTOMATION_READINESS.md` is an artifact, not source. It is force-added so the
   check ships with its evidence and stays out of the default ignore paths.
