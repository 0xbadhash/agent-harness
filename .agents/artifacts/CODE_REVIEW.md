# CODE-REVIEW

**Marker:** CODE-REVIEW
**Base:** 56a4b3c6ea620d8c637b165579f70a27825fbb85
**Head:** 6ea5fb1
**Command:** `python3 scripts/review_scope.py --base HEAD~1 --head HEAD --json`
**Verdict:** approve
**P0:** 0

## Scope

In this ship: `scripts/security_root_ioc_scan.py`, `tests/test_security_root_ioc_scan.py`, `deploy/security-root-ioc.service` (comment only), `docs/ship-flow.md` (one sentence), the spec, `CHANGELOG.md`, and `PR_DRAFT.md`.

Left unstaged on purpose: `.gitignore`, `config/optional_skills.txt`, `scripts/ops_dashboard.py`, `tests/test_ops_dashboard.py`, and untracked local files. They are not this item. `pipeline.json` is assume-unchanged and was not committed.

## Secrets

`python3 scripts/check_secrets_diff.py --base HEAD~1 --head HEAD` clean. `check_hardcodes.py` exit 0. No username path was added. `/home` and `/root` are the process-home rule, not a home directory of a person.

## Findings

| ID | Class | Verdict |
|----|--------|---------|
| P0 | none | approve |

Checked against the diff:

- Process home `/root` with no `--home` puts `/home` in the required list and still walks `/root`. A clean `/root` cannot be `status=ok`.
- `--home` replaces that list. It does not append to `/root`.
- A non-root process home is not widened to every account under `/home`.
- `status=ok` and the green artifact require every required home to be a directory that was entered. `PermissionError` on that walk leaves the home unscanned and yields `incomplete`, exit 2.
- `--print-roots` returns before the walk and before vault writes, and its text does not include `status=ok`.
- `--deep` still adds containerd. `--root` still appends. The timer's `SuccessExitStatus=0 1` does not treat exit 2 as success.
- Tests build homes with `Path("/home") / "operator"` and temp dirs. They do not walk `/home` or `/opt`.

## Follow-ups (not in this diff)

- `os.walk` still ignores permission errors on subdirectories (default `onerror`). A root scan of `/home` can skip an unreadable child and still look complete. That predates this change. Root on this host can read the product trees. Not an in-scope blocker.
- `scripts/ops_dashboard.py` already shows non-ok, non-fail JSON as attention. The working tree has unrelated edits, so this ship does not touch it.

## Tests

`TMPDIR=/tmp python3 -m pytest -q tests/test_security_root_ioc_scan.py` — 11 passed. `python3 scripts/validate.py full` — 6/6. Full pytest with `TMPDIR=/tmp` — 344 passed. With the session `TMPDIR` under `/home/.../cache`, two unrelated tests fail; that is the temp path, not this diff.
