# CODE-REVIEW

**Marker:** CODE-REVIEW
**Base:** HEAD~1
**Head:** HEAD (ae01b42)
**Scope:** scripts/retire_duplicate_night_shift_unit.py, tests/test_retire_duplicate_night_shift_unit.py, docs/night-shift.md, skills/night_shift/SKILL.md, CHANGELOG.md, PR_DRAFT.md
**Secrets:** check_secrets_diff.py HEAD~1...HEAD clean

## Verdict

Approve. P0 count: 0. No in-scope blocker.

## Findings

- P0: none. `apply_retirement` unlinks a path only when `path.name` is `night-shift-readiness.service` or `night-shift-readiness.timer`. A forged plan that points at `night-shift-all.timer` raises `ValueError` and leaves the file. Covered by `test_apply_refuses_a_path_outside_the_duplicate_names`.
- P0: none. `plan_retirement` returns `ok` false and an empty remove list when `night-shift-all.timer` is missing or the products text has no `watchlist` id. The CLI exits 2 before `--systemd` or unlink.
- Follow-up: `scripts/kanban_fs.py` has an unused `subprocess` import on this branch. That file is not in this diff. A local uncommitted edit already removes it. Not this item.
- Follow-up: vault schema lint reports pre-existing root and project errors, including `mission-feeds` missing from the committed registry. The registry line that adds it is an uncommitted edit outside this item. Do not edit the vault.

## Smoke / tests

- Red: pytest of the new file failed 7 tests with FileNotFoundError before the script existed. AC-6 passed because deploy/ has no duplicate unit.
- Green: `.venv/bin/python -m pytest -q tests/test_retire_duplicate_night_shift_unit.py` — 8 passed.
- Host: `systemctl list-timers --all 'night-shift*'` lists only `night-shift-all.timer` (enabled). `night-shift-readiness.timer` is not-found. Second `--apply --systemd` removed nothing and exited 0.
- Plugin smoke with `TMPDIR=/tmp`: hardcodes and unit smoke passed. The session `TMPDIR` is under `/home/debian/hermes/cache`, which makes two pre-existing tests fail; they pass under `/tmp`.

## Scope governor

No accepted P0. No second fix cycle. Diff stayed on the retire command, its tests, and the operator note.
