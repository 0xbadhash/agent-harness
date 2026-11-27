# PR Draft: Pristine garden: scratch artifacts and dirty tree fail the pack

**Range:** `origin/main..HEAD`

## What Problem This Solves

The harness asked product repos for a clean tree while its own tree carried
backup files, a coverage database, and uncommitted cross-window edits.
`check_repo_hygiene.py` only looked for `MagicMock` imports and orphan TODOs, so
scratch files passed the gate and agents copied what looked established.

## Why This Change Was Made

`/pr_review --validate` should refuse a ship whose working tree still holds
scratch state. The gate now names the offending path and, for the validate path,
the uncommitted entries.

## User Impact

- Operators see `hard_gates: repo_hygiene — fail: scratch artifact present: …`
  while scratch state remains.
- `/pr_review --validate` fails on a dirty tree; manual
  `python3 scripts/check_repo_hygiene.py` keeps the clean check off by default.
- `.gitignore` now lists the backup/scratch patterns.

## Evidence pack

| Gate | Command | Result |
|------|---------|--------|
| Red proof | `python3 -m pytest tests/test_repo_hygiene.py tests/test_hard_gates.py -q` | `15 failed, 12 passed` before implementation |
| Targeted tests | same command after implementation | `20 passed, 7 subtests passed` |
| Full suite | `python3 -m pytest -q` | `479 passed, 2 skipped` |
| Smoke | `python3 scripts/product_smoke.py --root .` | 2/2 steps passed |
| Validate | `python3 scripts/validate.py full` | 6/6 gates passed |
| Hard gates | `python3 scripts/pr_validator.py --diff origin/main...HEAD` | see PR body |

**Spec:** `.agents/specs/2026-11-27-pristine-garden-hygiene.md`
**Plan:** `.agents/specs/2026-11-27-pristine-garden-hygiene-plan.md`

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 `check` fails on each scratch pattern | `tests/test_repo_hygiene.py::TestScratchArtifacts::test_each_scratch_pattern_fails` |
| AC-2 dirty repo fails, committed repo passes | `tests/test_repo_hygiene.py::TestDirtyTree::test_dirty_repo_fails_when_required` |
| AC-3 hard_gates reports `repo_hygiene`; prose skips | `tests/test_hard_gates.py::test_repo_hygiene_blocks_code_ship`, `::test_repo_hygiene_skips_for_prose` |
| AC-4 `.gitignore` + no live `.bak-*` | `cat .gitignore`; `python3 scripts/check_repo_hygiene.py` (no scratch hits) |
| AC-5 full suite green | `python3 -m pytest -q` → 479 passed, 2 skipped |
| AC-6 smoke and validate | `product_smoke.py --root .` 2/2; `validate.py full` 6/6 |
| AC-7 no secrets | `check_secrets_diff.py` inside `hard_gates` |

## Threat notes

Security tags: `secrets`, `path-traversal`, `supply-chain`.

- Asset / trust boundary: the gate runs as the operator and executes only
  `git status --porcelain`; it reads no network and no credentials, so the
  `secrets` surface stays unchanged.
- Abuse case: a scratch path such as `../../x.bak-1` could aim at a resolved path
  outside the root; mitigation is `relative_to(root)` on every hit and
  `path-traversal` is covered by the pattern tests.
- Abuse case: a compromised tool could drop a `signal-cli-canary-*` or `.coverage*`
  file to mask state; the gate fails on those names and `.gitignore` keeps them
  out of the `supply-chain` commit surface.
- Abuse case: a dirty-tree block could stall local iteration; mitigation is
  `require_clean=False` as the default for manual runs, with the clean requirement
  enabled only inside `/pr_review --validate`.
- Abuse case: a non-repo fixture would fail closed incorrectly; mitigation is the
  warning-not-failure path covered by `test_non_repo_is_a_warning`.

## Red-proof (process honesty)

Red was observed before implementation: the same targeted command exited with
`15 failed, 12 passed`, including `AttributeError: module 'check_repo_hygiene' has
no attribute 'check'`. The retained green command is executable:

```text
green_cmd: python3 -m pytest tests/test_repo_hygiene.py tests/test_hard_gates.py -q
```

## Things that look bad but are actually fine

1. `check_repo_hygiene.py` still warns on three ticket-less TODOs in tests; the
   spec keeps that warning non-failing on purpose.
2. `bin/restore_product_venvs.sh` stays untracked and locally excluded; it is a
   restore tool, not scratch state.
3. The clean-tree check warns on a non-git fixture root so product fixtures that
   copy scripts keep working.
