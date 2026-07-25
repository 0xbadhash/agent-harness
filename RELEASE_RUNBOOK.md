# Release runbook — agent-harness v1.3.7

**Scope:** P1 behavior_validator, P2 handoff, P3 session tools, NEXT_SKILL handoff

## Smoke
- `python3 -m unittest tests.test_next_skill tests.test_review_scope tests.test_check_secrets_diff`
- `python3 scripts/validate.py full`
- `python3 scripts/next_skill.py --after execute_dev --base HEAD~1`

## Install products
```bash
for p in watchlist email-detach substack-push second-brain catalyxt.ltd ocr-ledger zk-business-card; do
  bash install_into_product.sh /home/debian/$p
done
```
