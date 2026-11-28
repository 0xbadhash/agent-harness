# CODE-REVIEW — top-50 gap closure

**Marker:** CODE-REVIEW
**Command / Scope:** `python3 scripts/review_scope.py --base origin/main --head HEAD --json`
→ 33 files, 1168 insertions, 139 deletions, `prose_only: false`
**Base:** `origin/main` `348ef6f`
**Head:** `HEAD` (branch `fix/top50-gaps`)

## Standards

- **Naming.** `check_glossary.Report` and `Comment finding`/`Comment route` match
  the glossary. `route_comment`, `classify_constraint`, `background_argv`, and
  `record_session` state the action and the object.
- **Duplication.** The none-with-a-note rule lives in `check_ticket_dag._ids` and
  `spec_gate.check_ticket_blocking_edges`; both are three lines and read the same
  template phrase, so a shared module would add an import across a portable
  script boundary.
- **Complexity.** `main` in `check_comment_audit.py` gained one branch for
  `--classify`/`--constraints`; the diff-scoped row helpers keep the two modes on
  one row shape. No new suppression.
- **Error handling.** `check_glossary` returns a `Report` with `skip` or
  `findings`; `hard_gates` appends a violation or a skip reason. `weekly_retro`
  returns 0 with a printed reason when no run records exist.
- **Types.** `mypy scripts tests` reports no issues after the row-shape and
  optional-path fixes.

## Findings

- **P1 (fixed before review close):** `mypy` rejected the early `rows` binding in
  `check_comment_audit.main` because it reused the name for two tuple shapes.
  Renamed to `comment_rows`.
- **P1 (fixed before review close):** `check_glossary.main` read `report.path.name`
  without narrowing the optional path. Added a guard.
- **P2 (accepted):** `--constraints` is noisy on a whole-tree run (110 comments).
  It is opt-in and intended for a ship diff; the spec records promotion as out of
  scope.
- **P2 (accepted):** `background_argv` strips `--background` by exact match. The
  flag is `store_true`, so there is no `--background=value` form to carry.

## Correction checks

- P1 tuple-shape mypy error → `python3 -m mypy scripts tests` and
  `python3 scripts/validate.py full`
- P1 optional-path mypy error → `python3 -m mypy scripts tests`
- P2 `--constraints` whole-tree noise → `tests/test_comment_audit.py::TestConstraintCheck`
- P2 `--background` argument stripping → `tests/test_stack_runners.py::test_background_argv_drops_only_the_flag`

## Verdict

Approve. Tests, mypy, lint ratchet, hard gates, and `validate.py full` are green.
