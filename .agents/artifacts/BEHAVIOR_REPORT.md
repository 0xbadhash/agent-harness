# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** .agents/artifacts/BEHAVIOR_CONTRACT.md
**Target:** vault schema lint CLI, product registry, ruff

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1. Live vault schema lint exits 0 | pass | `validate.py full` ran `vault_schema_lint` and printed `schema-lint: 0 error(s), 0 warning(s)` then `vault_schema_lint passed` |
| 2. mission-feeds row is portable | pass | Registry line is `mission-feeds: ~/.local/lib/mission-feeds` |
| 3. No live `01-Projects/product` directory | pass | `test ! -d /opt/second-brain/vault/01-Projects/product` succeeded (`product folder absent`) |
| 4. ruff clean | pass | `.venv/bin/python -m ruff check scripts tests` exit 0 |

## Summary

- pass: 4 · fail: 0 · blocked: 0
- NEXT_SKILL=/pr_review --validate
