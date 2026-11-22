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

---

# CODE-REVIEW — vault completion writer (2026-11-09)

**Marker:** CODE-REVIEW · **Range:** HEAD~2...HEAD (commits 97a4c8d, 62c7f4a) · **Secrets:** clean
**Engine:** self-review against the plan's own acceptance criteria (no second model available in this lane).

Findings accepted and fixed in-range:
1. **Unused imports** (shutil, os, subprocess) — caught by the linter gate, fixed in 62c7f4a.
2. **A test asserted a trailing space was illegal inside quotes** — wrong assertion; corrected to allow it inside
   quotes and only forbid it outside. The implementation was right, the test was not.

Findings verified, not defects:
- `os.replace` inside the spool is same-filesystem by construction (temp file created in the spool).
- The processed copy uses `O_EXCL` + `chmod 0444`; the spool inode is unlinked only after that succeeds.
- `yaml_quote` covers U+2028/U+2029/U+0085, tab, backslash, quote and C0 controls; the body renderer escapes
  `& < ` ~` so no fence can form.

**P0 = 0 · P1 = 0 · follow-ups: none open.**

---

# CODE-REVIEW — night-gate golden-drift (2026-11-15)

**Marker:** CODE-REVIEW
**Base:** working tree before this slice (branch `docs/ops-dashboard-contract`)
**Head:** uncommitted edits in `scripts/check_hardcodes.py`, `scripts/watchlist_golden_drift.py`, `tests/test_check_hardcodes_skips.py`, `tests/test_watchlist_golden_drift.py`, `CHANGELOG.md`
**Engine:** same-session review. No second model was invoked. Unrelated dirty files (ops dashboard, challenge, PR_DRAFT) were not part of this slice.

## Secrets

No credential, token, or new absolute home path. The new allow-list entries are the public hosts `query1.finance.yahoo.com` and `finance.yahoo.com`. Unknown hosts stay failing (`test_real_src_url_still_flagged`).

## Verdict

Approve this slice. P0 = 0.

## Findings

- No in-scope blocker. The RSI loop rebinds `loss` only after the seed average is taken, same as the old `l`. The dated-name unlink loop is unchanged; the removed `same` list was unused.
- Follow-up, not this slice: `.hardcode-allow.json` still prints three allowed `/home/browser` container paths. They are not violations. Deleting them was not done.
- Pipeline was not advanced. `PR_DRAFT.md` still describes the vault completion writer.

## Tests

`pytest tests/test_check_hardcodes_skips.py` 4 passed. `mypy scripts tests bin` exit 0. `ruff check scripts tests` exit 0. `validate.py full` 6/6. `product_smoke.py` 2/2.

---

# CODE-REVIEW — collect_and_learn run_one args (2026-11-20)

**Marker:** CODE-REVIEW
**Base:** `HEAD` (`33aa8c5`)
**Head:** uncommitted edits in `bin/night_shift_all_products.py`, `tests/test_night_refresh_from_orchestrator.py`, and the matching `CHANGELOG.md` subsection
**Spec waiver:** hotfix (type-checker defect). Not written into `PR_DRAFT.md` — that draft is the unfinished vault completion writer.
**Engine:** same-session review. No `CODE_REVIEW_MODEL` / `GROK_MODEL_CROSS_REVIEW` is set.

## Secrets

`python3 scripts/check_secrets_diff.py --base HEAD --head HEAD` → clean. This slice adds no credential, token, or host.

## Verdict

Approve this slice. P0 = 0.

## Findings

- No in-scope blocker. `collect_and_learn` now passes `vault`, `quick`, `skip_live`, and `dry_run` into `run_one`. Production `main` already did. Defaults are dry-run and skip-live so the test stand-in cannot start a live gate. An omitted vault is the artifact directory, and only on this stand-in.
- Follow-up, not this slice: the working tree still holds unrelated uncommitted edits (ops dashboard, challenge routing, golden-drift, vault-writer PR draft). They were left untouched. Pipeline phase stays `init` on task `vault-completion-writer`.

## Tests

Red: `test_collect_and_learn_forwards_gate_args_to_run_one` raised `TypeError: unexpected keyword argument 'vault'`.
Green: `pytest tests/test_night_refresh_from_orchestrator.py` → 3 passed.
`mypy scripts tests bin` → exit 0.
`ruff check` on the two Python files → exit 0.
`python3 scripts/validate.py full` → 6/6, including type_checker exit 0.

---

# CODE-REVIEW — security-root-ioc real homes (2026-11-22)

**Marker:** CODE-REVIEW
**Base:** `6ea5fb1` (parent-`/home` requirement) plus the working tree for this slice
**Head:** uncommitted slice on `main` before the item commit
**Scope:** `scripts/security_root_ioc_scan.py`, `tests/test_security_root_ioc_scan.py`, `deploy/security-root-ioc.service` comment, `docs/ship-flow.md` sentence, spec and plan. Not `scripts/ops_dashboard.py`.

## Secrets

No credential, token, or username. Homes are child directories of `/home` discovered at run time. `check_hardcodes.py` reported no hardcodes.

## Verdict

Approve. P0 = 0.

## Findings

- No in-scope blocker. `resolve_home_roots` now requires each child directory when the process home is `/root`. The parent is not a scan root and is not required when children exist. An empty or unlistable parent stays required and unscanned, so the status is `incomplete`. `--home` still replaces discovery. `/root` is still walked and is not sufficient.
- Follow-up, not this slice: `os.walk` still ignores permission errors below the top of a required home. A nested unlistable directory can hide a pin once the home itself was entered. The assigned bug is the home directory, not every nested folder.
- Follow-up: a `status=fail` scan calls `ops_dashboard --write` even with `--no-artifact`. That is the previous behavior. This review did not change it. The IoC JSON and markdown in the vault were not rewritten (mtime 2026-11-20).

## Tests

Red: five tests raised `TypeError` on `multiuser_home` (`pytest` 5 failed, 8 passed).
Green: `pytest tests/test_security_root_ioc_scan.py` → 13 passed.
`mypy scripts/security_root_ioc_scan.py tests/test_security_root_ioc_scan.py` → exit 0.
`ruff check` on those two files → passed.
