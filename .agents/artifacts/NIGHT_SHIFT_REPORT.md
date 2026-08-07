# Night shift readiness — agent-harness — 2026-08-06 20:18 UTC · 2026-08-07 04:18 HKT

**When:** 2026-08-06 20:18 UTC · 2026-08-07 04:18 HKT
**Overall:** FAIL (5/6 gates) · mode=`full+autofix` · product=`agent-harness`
**Repo:** `/home/debian/agent-harness`
**Hard-stops:** no release/tag/force-push; autofix is mechanical only (deps/format)
**SoT:** agent-harness `scripts/night_shift_readiness.py`

## Gates

| Gate | Result | Exit |
|------|--------|------|
| repo_hygiene | ✅ | 0 |
| hardcodes | ✅ | 0 |
| verify_skills | ✅ | 0 |
| validate_full | ❌ | 1 |
| product_smoke | ✅ | 0 |
| coverage | ✅ | 0 |

## Failures (tails)

### validate_full
```
❌ type_checker (exit 1)
❌ linter (exit 1)
✅ test_runner (exit 0)
✅ no hardcodes
⚠️  tests/test_night_shift_morning_triage.py:21 TODO without ticket ref
✅ repo hygiene ok
✅ coverage config valid (default 10%, fail_under 10%, 3 overrides)
✅ dev-log contract OK (1 project log(s))

── compliance_engine ──
❌ compliance_engine failed (exit 1)

── check_hardcodes ──
✅ check_hardcodes passed

── check_repo_hygiene ──
✅ check_repo_hygiene passed

── check_module_coverage ──
✅ check_module_coverage passed

── check_dev_log_contract (vault=/opt/second-brain/vault, project=agent-harness) ──
✅ check_dev_log_contract passed

========================================
4/5 gates passed

```



## Auto-fix attempts (bounded)

- `ensure_dev_env` → **ok** — imports ok via /home/debian/watchlist/.venv/bin/python
- `ruff_fix` → **fail** — ruff check --fix (scripts/tests/src)

## Recommendations

1. [agent-harness] Auto-fix `ensure_dev_env` → ok: imports ok via /home/debian/watchlist/.venv/bin/python
2. [agent-harness] Auto-fix `ruff_fix` → fail: ruff check --fix (scripts/tests/src)
3. [agent-harness] Run `python3 scripts/validate.py full`; fix type/lint/test/hardcode.
4. [agent-harness] PROPOSE confidence=0.85 kind=fix lean=defect | clear validate full (type/lint/test/hardcode) before next /execute_dev | evidence: validate_full exit=1; ❌ type_checker (exit 1) ❌ linter (exit 1) ✅ test_runner (exit 0) ✅ no hardcodes ⚠️  tests/test_night_shift_morning_tria
5. [agent-harness] PROPOSE confidence=0.72 kind=refactor lean=rework | refactor: resolve in-code TODO/FIXME flagged by gates | evidence: gate `validate_full` tail pattern match; snippet:  ❌ type_checker (exit 1) ❌ linter (exit 1) ✅ test_runner (exit 0) ✅ no hardcodes
6. **Human hard-stop:** do not `/release_mgmt` or push unreviewed fixes from night_shift.
