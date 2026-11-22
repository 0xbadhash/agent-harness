# CODE-REVIEW

**Marker:** CODE-REVIEW
**Base:** `release/v1.4.49-gpa` (HEAD before this docs slice)
**Head:** working tree on `docs/ops-dashboard-contract`
**Scope:** `deploy/ops-dashboard.service`, `deploy/ops-dashboard.timer`, `tests/test_ops_dashboard_contract.py`, spec, PR draft. Installed unit comments and the vault inventory row are host text, not this git diff.

## Secrets

No new credential, URL, or token. Comments name the existing `ExecStart` script and the inventory path. `check_secrets_diff` is run on the commit range before approve.

## Verdict

Approve. P0 = 0.

## Findings

- No in-scope blocker. `SuccessExitStatus=0 2` and the two base `OnCalendar=` lines are unchanged. The new sentences say exit 2 is an intentional RED and that the timer is enabled with four calendars.
- Follow-up, not this slice: repo `Group=debian` still differs from the installed `Group=secondbrain`. Reconciling it would change the vault write. Left as-is.
- Follow-up: `scripts/ops_dashboard.py` was stashed because it already had an unrelated uncommitted rewrite. This review does not include that file.

## Tests

`python3 -m pytest -q tests/test_ops_dashboard_contract.py` — 3 failed before the sentences, 4 passed after. `ruff check` on the new test passed.
