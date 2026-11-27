# CODE-REVIEW — pristine garden hygiene

**Marker:** CODE-REVIEW

- Command: `python3 scripts/next_skill.py --after execute_dev --base origin/main --head HEAD`
- Base: `origin/main` · Head: `HEAD`
- Secrets scan: covered by `hard_gates` (`check_secrets_diff.py`)

## Standards

- `check_repo_hygiene.check` follows the established `(ok, messages)` contract
  used by the other gate checkers, with `fail:` and `warn:` prefixes.
- `scan_scratch_artifacts` is a single `rglob` pass that reuses `SKIP_DIRS`;
  `_magicmock_hits` and `_todo_hits` reuse `_iter_files` instead of duplicating
  traversal logic.
- `hard_gates` adds the call in the same guarded `try/except` style as the other
  gates and lists `repo_hygiene (prose-only)` in the skip set.
- The CLI keeps `--require-clean` opt-in, so manual hygiene runs stay usable on a
  working tree while `/pr_review --validate` enforces the clean requirement.
- No P0 findings.

## Spec

- AC-1 and AC-2 are covered by `tests/test_repo_hygiene.py`.
- AC-3 is covered by `tests/test_hard_gates.py::test_repo_hygiene_blocks_code_ship`
  and `::test_repo_hygiene_skips_for_prose`.
- AC-4 is `.gitignore` plus the existing `night_shift_runtime.yaml.bak-t1659u`
  removal; `check_repo_hygiene.py` on the repo reports no scratch hits.
- AC-5 through AC-7 are the full suite, smoke, validate, and the diff secrets scan.
- Scope matches the spec; no unrelated cleanup was folded in.

## Correction checks

- Scratch suffixes could pass unnoticed → tests/test_repo_hygiene.py
- A dirty tree could still validate → tests/test_repo_hygiene.py::TestDirtyTree
- The gate could be wired but not reported → tests/test_hard_gates.py
- Prose ships could be blocked by a code gate → tests/test_hard_gates.py
- Non-repo fixtures could fail closed → tests/test_repo_hygiene.py::test_non_repo_is_a_warning

## Findings

- P0: none.
- Follow-ups: none required for this slice. A future item could promote the
  ticket-less TODO warning to a ratchet, which is out of scope here.

## Verdict

Approve. The change is local to the harness gate pack, the new tests went red
before the implementation and green after, and the full suite, smoke, and
validate are green.
