# PR Draft — Portable review improvements (openclaw-inspired)

**Date:** 2026-07-25  
**Version:** 1.3.4  

## What Problem This Solves

Agents inflate PRs on review nits, re-review with the same model, skip secret scans on diffs, and treat green review as product proof. openclaw autoreview has strong ideas; we need them **without** vendoring a 12k-line multi-engine CLI.

## Why This Change Was Made

Adopt: scope governor, P0-first, optional `/code_review`, diff secrets scan, prose-only skip, re-review-after-fix, behavior≠source smoke pairing — in harness-owned skills/scripts.

## User Impact

Clearer ship reviews; optional second-model pass; fail closed on secret-like additions; less process theater for pure internal prose.

## Evidence

- `python3 -m unittest tests.test_review_scope tests.test_check_secrets_diff` — OK  
- `python3 scripts/validate.py full` — 5/5  
- `python3 scripts/product_smoke.py` — OK  

## Red-proof

- green_cmd: `python3 -m unittest tests.test_review_scope tests.test_check_secrets_diff -q`

## Cross-review

`.agents/artifacts/CROSS_REVIEW.md` — blockers=0

## Things that look bad but are actually fine

1. No full OpenClaw isolation matrix — portable by design.  
2. Regex secret scan is narrower than TruffleHog verified mode — intentional fallback.  
3. code_review does not advance pipeline — pr_review still owns phase.  
4. F401 fix in normalize_vault_devlog is drive-by lint — required for validate green.  
5. Single release for all adopted ideas — one coherent vertical slice.
