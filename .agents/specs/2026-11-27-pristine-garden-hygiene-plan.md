# Plan — pristine garden hygiene gate

**Spec:** `.agents/specs/2026-11-27-pristine-garden-hygiene.md`

## Approach

Keep one dependency-free checker module, expose the `(ok, messages)` contract the
gate pack already uses, and wire it into `hard_gates` for non-prose ships. The
clean-tree requirement is opt-in at the module level and on for `/pr_review`, so
manual runs stay usable on a working tree.

## Architecture

- `scripts/check_repo_hygiene.py` owns `SCRATCH_PATTERNS`, `scan_scratch_artifacts`,
  `_git_dirty`, and `check(root, *, require_clean=False)`.
- `scripts/hard_gates.py` calls `check(root, require_clean=True)` inside the same
  guarded block as the other local checks and records a prose-only skip.
- `.gitignore` mirrors the scratch patterns so ignored state and the gate agree.
- Tests split unit behavior (temp trees, temp git repos) from gate wiring.

## Implementation sequence

1. Write `tests/test_repo_hygiene.py` and the two `hard_gates` integration tests.
2. Refactor `check_repo_hygiene.py` to the `check()` contract and add the patterns.
3. Wire `hard_gates`, update `.gitignore`, and run targeted plus full verification.

## Risks and rollback

- Risk: the dirty-tree block could stop local iteration. Mitigation: default off
  outside `/pr_review`; delete the `hard_gates` call to roll back.
- Risk: novel scratch suffixes slip through. Mitigation: add a pattern and a test
  case in one line.
