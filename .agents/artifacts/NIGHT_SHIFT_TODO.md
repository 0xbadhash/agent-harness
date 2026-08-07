# agent-harness TODO (night_shift readiness)

_Auto-updated by harness `night_shift_readiness.py` at **2026-08-06 20:18 UTC · 2026-08-07 04:18 HKT**. Overall: **FAIL**._

Do **not** hand-edit the auto section; add notes under **Human backlog**.

## Auto recommendations (from last night shift)

- [ ] [agent-harness] Auto-fix `ensure_dev_env` → ok: imports ok via /home/debian/watchlist/.venv/bin/python
- [ ] [agent-harness] Auto-fix `ruff_fix` → fail: ruff check --fix (scripts/tests/src)
- [ ] [agent-harness] Run `python3 scripts/validate.py full`; fix type/lint/test/hardcode.
- [ ] [agent-harness] PROPOSE confidence=0.85 kind=fix lean=defect | clear validate full (type/lint/test/hardcode) before next /execute_dev | evidence: validate_full exit=1; ❌ type_checker (exit 1) ❌ linter (exit 1) ✅ test_runner (exit 0) ✅ no hardcodes ⚠️  tests/test_night_shift_morning_tria
- [ ] [agent-harness] PROPOSE confidence=0.72 kind=refactor lean=rework | refactor: resolve in-code TODO/FIXME flagged by gates | evidence: gate `validate_full` tail pattern match; snippet:  ❌ type_checker (exit 1) ❌ linter (exit 1) ✅ test_runner (exit 0) ✅ no hardcodes
- [ ] **Human hard-stop:** do not `/release_mgmt` or push unreviewed fixes from night_shift.

## Last gate snapshot

- [x] `repo_hygiene` (exit 0)
- [x] `hardcodes` (exit 0)
- [x] `verify_skills` (exit 0)
- [ ] `validate_full` (exit 1)
- [x] `product_smoke` (exit 0)
- [x] `coverage` (exit 0)

## Human backlog

- [ ] 
