# BEHAVIOR-REPORT — product-trait categories
**Marker:** BEHAVIOR-REPORT  
**Verdict:** PASS  

## Observed
- Dry miss: `python3 scripts/check_product_traits.py --root fixtures/product_traits/web3_no_isolation` → EXIT 1.
- Web-only fixture: isolation stubs not required → PASS.
- Harness SoT (`traits.web3/client_secrets/web=false`): check_product_traits EXIT 0.
- Unit: `tests.test_product_traits` (6) green.
