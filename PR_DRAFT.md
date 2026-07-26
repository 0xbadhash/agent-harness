# PR Draft: v1.4.0 any-LLM bootstrap + install verify

**Range:** v1.3.7..HEAD

## What Problem This Solves

Products and LLMs needed a clearer, testable way to install the full ship-skill FSM without guessing skill paths or missing chain steps.

## Why This Change Was Made

1. `install_into_product.sh --verify` + `bootstrap_check.sh`  
2. `verify_skills.py` dual-root + ship-chain manifest  
3. `docs/llm-bootstrap.md` + AGENTS template  
4. Install copies FSM docs into `.agents/docs/`  
5. Unittest install smoke (temp product)

## User Impact

Any LLM can bootstrap a product and run full FSM with documented one-shot phrases and gates.

## Evidence

```text
green_cmd: bash scripts/run_harness_tests.sh
green_cmd: python3 scripts/verify_skills.py .
green_cmd: bash scripts/bootstrap_check.sh .
```

## Things that look bad but are actually fine

1. pytest suite still optional without venv — bootstrap tests use stdlib unittest.  
2. Soft AGENT_REFERENCE warnings reduced on harness SoT skills.  
3. Product-only skills preserved on re-install (rsync).  
4. VERSION minor bump 1.4.0 for bootstrap contract.  
5. No product application code in harness.  
