# CROSS-REVIEW

**Marker:** CROSS-REVIEW
**Range:** `a463eef..HEAD` (`fa8226b`)
**Secrets:** `check_secrets_diff.py --base HEAD~1 --head HEAD` clean.
**Blockers:** 0
**Tier A obsolete:** 0

## Security Guru

None. The diff does not add a credential, a vault write, or a new network call. `test_unset_vault_calls_no_model` now drops `PRODUCT_VAULT_ROOT` before `challenge.main`, which is what stopped a night-shift process from treating the operator vault as the fixture vault. The CLI still refuses an unset vault before any model call (stderr: `pre-flight failed, no model was called`).

## Maintainability Expert

None. The env save/restore matches `test_unset_vault_refuses_instead_of_host_default` in the same file. The fixture splits keep the runtime strings the assertions already require. No production module moved.

### Obsolete / cleanup (scoped)

Touched paths only: the four tests, `PR_DRAFT.md`, `CODE_REVIEW.md`, `BEHAVIOR_REPORT.md`.

| Item | Conf | Verdict | Evidence |
|------|-----:|---------|----------|
| `tests/test_challenge.py` preflight test | 0.1 | Tier C keep | Pytest collects `ChallengePreflightTests`. `scripts/challenge.py` `_rounds` is the callee the night-shift failure hit. |
| Fixture `# TODO` splits in three tests | 0.1 | Tier C keep | `check_repo_hygiene.py` warns on the unsplit form. Comment-auditor test still expects one ownerless TODO. |
| `scripts/challenge.py` | 0.0 | Tier C keep | Not in the diff. Still the CLI `product_smoke` does not call directly; unit smoke imports it via pytest. |

No Tier A. No Tier B. Whole-repo cruft is out of scope — run `/sweep`.

## Domain Specialist

None. Plugin hints are a portable harness and no secret leakage. Smoke commands stayed `check_hardcodes.py` and `scripts/smoke_unit.sh`. The harness does not gain a host path or a new smoke step.

## Severity

- blocker: 0
- major: 0
- nit: 0
- follow-up: hygiene could skip string literals so fixtures need not split `# TODO`. Not a ship blocker.

## Things that look bad but are actually fine

1. Popping `PRODUCT_VAULT_ROOT` is the unset-vault case, not a deleted assertion.
2. Split `# TODO` literals still produce the same runtime headings.
3. `challenge.py` stays as it is because a set vault is supposed to reach the models.
