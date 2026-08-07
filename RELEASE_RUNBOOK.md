# RELEASE RUNBOOK — v1.4.18 mandatory web/app E2E

**Score:** 100 · **Waiver:** chore

## Shipped
- Fail-closed `check_web_e2e` for website/browser-app products
- S-id sync Playwright ↔ Comet; surfaces + smoke e2e required
- README, ship-flow, install_into_product Web E2E check
- portfolio install guidance

## Smoke
| Step | Exit |
|------|------|
| pytest tests/test_web_e2e_contract.py | 0 (11) |
| ruff/mypy on web_e2e scripts | 0 |
| pr_validator | 100 |

## Rollback
`git checkout v1.4.17`

## §9
1. substack-push opts out (CLI + Playwright transport).
2. S-id presence is lexical match in Comet doc.
3. install warns on fail but does not abort install (product can finish fixing).
