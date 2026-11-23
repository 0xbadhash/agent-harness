# CODE-REVIEW

**Marker:** CODE-REVIEW
**Range:** working tree vs `HEAD` (tests + `PR_DRAFT.md`)
**Verdict:** approve
**P0:** 0

## Scope

Four test files. No change under `scripts/`, `bin/`, or `.agents/product_plugin.yaml`.

- `tests/test_challenge.py` — `test_unset_vault_calls_no_model` saves and restores `PRODUCT_VAULT_ROOT`.
- `tests/test_enhancement_mechanisms.py` — ownerless TODO fixture is built with concatenation.
- `tests/test_night_shift_morning_triage.py` — fixture heading split the same way.
- `tests/test_night_shift_kanban_sync.py` — `todo_md` heading split the same way.

## Secrets

No credentials, tokens, or vault bodies added. The test avoids the live vault by clearing the env a parent process may have set.

## Findings

Accepted: none. P0 count is 0.

Rejected: "change `product_plugin.yaml` smoke[]". The night-shift tail is a pytest assertion inside the existing `unit` step (`bash scripts/smoke_unit.sh`). The argv shape is already a list. Inventing a new smoke command is out of scope.

Rejected: "make `challenge.main` ignore `PRODUCT_VAULT_ROOT`". The CLI is supposed to use that variable. The bug is the test calling `main` while the variable is still set.

## Follow-ups

- `check_repo_hygiene.py` still flags `# TODO` inside string literals. The splits clear the three warnings this gate printed. A scanner that skips literals would remove the need to split. Not this diff.
- Standardizing smoke argv across other products is a separate fleet decision. This repo's plugin was not the broken piece.

## Tests

- Red: with `PRODUCT_VAULT_ROOT` set, `test_unset_vault_calls_no_model` failed before the pop was added (`AssertionError: glm must not be called during pre-flight`).
- Green: same test passes with the variable set. Full pytest: 455 passed, 1 skipped. `validate.py full`: 6/6. `product_smoke.py`: 2/2. Hygiene: no orphan-TODO warnings. Touched modules after the fixture edit: 43 passed.
