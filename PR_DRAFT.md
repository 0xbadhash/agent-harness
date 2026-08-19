# PR Draft — product-trait fail-closed test categories

**Spec waiver:** chore  
**Version target:** 1.4.35  

## What Problem This Solves
Ships could pass hard_gates without isolation or secret-wall coverage when the product is clearly web3 or client-secrets shaped (Card / BIP39-class). Scaffold previously emitted tautological `body.toBeVisible()` stubs without S-ids.

## Why This Change Was Made
CEO: infer required test categories from product traits; fail closed if missing; scaffold named stubs. Harness SoT only — no product VERSION bumps, no portfolio broadcast.

## User Impact
- Declare `traits:` in product_plugin or rely on auto-infer
- web3 → isolation S-id required (Comet + Playwright)
- client_secrets → property_tests on crypto modules + secret-wall S-id
- web-only products are not forced to grow isolation stubs
- `scaffold_web_e2e.py --write` adds named `test.skip("S…")` stubs with contracts

## Red-proof
- red_cmd: `python3 scripts/check_product_traits.py --root fixtures/product_traits/web3_no_isolation`
- green_cmd: `python3 -m unittest tests.test_product_traits -v`

## Traceability
| AC | Test / smoke |
|----|--------------|
| AC-1 web3 without isolation S-id fails closed | tests/test_product_traits.py::test_dry_miss_web3_without_isolation_exits_1 |
| AC-2 web-only does not require isolation | tests/test_product_traits.py::test_web_only_does_not_require_isolation |
| AC-3 scaffold named stubs not tautological | tests/test_product_traits.py::test_named_stub_not_tautological |
| AC-4 hard_gates wires product_traits | scripts/hard_gates.py + check_product_traits |
| smoke | python3 -m unittest tests.test_product_traits -v |

## Threat notes
- authz: isolation category targets IDOR / wrong-holder paint
- secrets: client_secrets category targets mnemonic/seed export and session leak
- abuse: trait false-negatives mitigated by explicit `traits.*: true` override

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator |
| unittest | tests/test_product_traits.py |
| dry miss | web3 no isolation EXIT 1 |
| validate | check_product_traits on harness SoT (traits off) |

## Things that look bad but are actually fine
1. Night-bar `73c2221` stays unpushed (branch from origin/main)
2. No portfolio `--install` in this ship (CEO: harness SoT only)
3. Does not reopen product PASSes or bump product VERSIONs
