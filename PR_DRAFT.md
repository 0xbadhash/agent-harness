# PR Draft: Categorical lint bans and typed suppressions

**Range:** `origin/main..HEAD`

## What Problem This Solves

`ruff.toml` selected only `E`, `F`, and `W`, so blind exceptions, mutable
defaults, `shell=True`, and runaway complexity passed the local gate. The tree
carried 95 type suppressions with no owner or expiry, and raw `ruff check` in
`compliance_engine.py` would fail as soon as new families were enabled.

## Why This Change Was Made

The gate should eliminate a construct category in configuration instead of asking
reviewers to catch it. The ratchet freezes the legacy counts, the suppression ban
is absolute, and the eight real mypy errors are fixed with typed annotations.

## User Impact

- A new blind except, over-complex function, mutable default, or `shell=True` call
  fails `check_lint_ratchet.py` and `validate.py full`.
- A new type suppression must name `[code]`, `owner=…`, and a future
  `expires=…`; expired suppressions fail.
- `compliance_engine.py` uses the ratchet as the lint gate, so local and CI signals
  agree.
- 87 unnecessary suppressions are gone; no runtime behavior changes.

## Evidence pack

| Gate | Command | Result |
|------|---------|--------|
| Red proof | `python3 -m pytest tests/test_type_ignores.py tests/test_lint_config.py -q` | `ModuleNotFoundError: check_type_ignores` before implementation |
| Targeted tests | same command after implementation | 24 passed |
| Mypy | `python3 -m mypy scripts tests` | Success: no issues in 217 files |
| Lint ratchet | `python3 scripts/check_lint_ratchet.py` | four rules held at baseline |
| Full suite | `python3 -m pytest -q` | 507 passed, 2 skipped |
| Smoke | `python3 scripts/product_smoke.py --root .` | 2/2 steps passed |
| Validate | `python3 scripts/validate.py full` | 9/9 gates passed |
| Hard gates | `python3 scripts/pr_validator.py --diff origin/main...HEAD` | pr_validator score 100 |

**Spec:** `.agents/specs/2026-11-27-categorical-lint-bans.md`
**Plan:** `.agents/specs/2026-11-27-categorical-lint-bans-plan.md`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 families and threshold | `tests/test_lint_config.py` |
| AC-2 ratchet floor | `tests/test_lint_ratchet.py`, `check_lint_ratchet.py` |
| AC-3 suppression ban | `tests/test_type_ignores.py` |
| AC-4 tree has no suppressions | `mypy scripts tests` success; grep finds none |
| AC-5 gate wiring | `tests/test_hard_gates.py::test_type_ignores_blocks_code_ship` |
| AC-6 compliance/validate | `validate.py full` 9/9 |
| AC-7 suite/smoke/secrets | full pytest 507 passed; smoke 2/2; `check_secrets_diff.py` |

## Threat notes

Security tags: `supply-chain`, `secrets`, `injection`.

- Asset / trust boundary: lint and mypy run locally on repository text; no network
  or credential access.
- Abuse case: a blanket suppression could hide a future injection defect; the ban
  forces a code, owner, and expiry so the suppression is reviewable
  (`supply-chain` integrity).
- Abuse case: `shell=True` was the named danger; `S602` is selected, and the tree
  has zero occurrences.
- Abuse case: a ratchet could hide new findings in an already-counted rule; the
  count is per rule and any increase fails.
- Abuse case: an expired suppression could mask a real type error; the checker
  compares `expires=` with today (`secrets`-adjacent reviewability).

## Red-proof (process honesty)

Red was observed before implementation: the targeted run failed collection with
`ModuleNotFoundError: No module named 'check_type_ignores'`, and `ruff check
--select B,BLE,S602,C90` reported 60 findings before the baseline was recorded.
The retained green command is executable:

```text
green_cmd: python3 -m pytest tests/test_type_ignores.py tests/test_lint_config.py tests/test_hard_gates.py -q
```

## Things that look bad but are actually fine

1. `BLE001=44` and `C901=14` remain in the baseline. The ratchet freezes them; the
   spec names the follow-up.
2. Removing 87 suppressions looks large; `mypy` is clean and the full suite is
   green, so the annotations were already unnecessary.
3. `compliance_engine` no longer calls raw `ruff check` when the ratchet exists;
   products without the script keep the old path.
4. `check_type_ignores.py` skips `.agents`, `.venv`, and cache directories, so
   generated trees do not fail.
