# Release runbook — agent-harness v1.3.5

**Scope:** execute_dev requires /code_review for non-prose ships; reinstall products.

## Smoke
- unittest review helpers  
- validate.py full  

## Install into products
```bash
for p in watchlist email-detach substack-push second-brain catalyxt.ltd agent-harness ocr-ledger zk-business-card; do
  bash install_into_product.sh ~/$p 2>/dev/null || bash install_into_product.sh /home/debian/$p
done
```
