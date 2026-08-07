# PR Draft: v1.4.18 mandatory website/app E2E

**Spec waiver:** chore  
**Range:** origin/main…HEAD (v1.4.18)

## What Problem This Solves

Agents shipped browser UI without systematically updating Playwright and Comet/Perplexity scenarios; soft warnings were ignored at score time.

## Why This Change Was Made

Fail closed when a website or browser app is detected: Playwright config + specs, S-ids in test titles matching Comet doc, `web_e2e.surfaces`, and `smoke[]` e2e. Document and install path make the rule mandatory portfolio-wide.

## User Impact

- `/pr_review` and `/release_mgmt` block incomplete web products  
- `install_into_product.sh` prints Web E2E check result after install  
- CLI products mis-detected can set `web_e2e.enabled: false`  
- README / ship-flow / web-e2e-comet.md describe the contract  

## Evidence

- `pytest tests/test_web_e2e_contract.py` → 11 passed  
- Portfolio: bip39lab, catalyxt-website, zk-business-card pass; substack-push opted out  

## Traceability

| AC | Test / smoke |
|----|----------------|
| Website without Playwright fails gate | `test_validate_fails_without_artifacts` |
| Full contract passes | `test_validate_passes_full_contract` |
| S-id missing from Comet fails | `test_playwright_sid_missing_from_comet_fails` |
| Opt-out works | `test_opt_out_enabled_false` |
| Install surfaces web check | `install_into_product.sh` Web E2E lines |

## Threat notes

- Gate does not execute browser tests itself — only contract presence/sync; product smoke still runs e2e.  
- Opt-out `enabled: false` is explicit so CLI tools using Playwright as transport are not forced into Comet UI contract.  

## Red-proof

```text
red_cmd: product with only web/index.html → check_web_e2e fails
green_cmd: pytest tests/test_web_e2e_contract.py -q → 11 passed
```

## Evidence pack

- hard_gates after PR_DRAFT complete  
- pytest web_e2e_contract  
- portfolio install + check_web_e2e on bip39lab/catalyxt/zk  

## Things that look bad but are actually fine

1. **substack-push** has Playwright in package.json but sets `web_e2e.enabled: false` — automation transport, not product website.  
2. **S-id sync** is presence in Comet text, not prose quality of every scenario.  
3. **strict: false** exists for migration only, not default ship.  
