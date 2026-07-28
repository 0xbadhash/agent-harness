# PR Draft — night_shift P0–P2 readiness hardening

**Date:** 2026-07-28  
**Version:** 1.4.2

## What Problem This Solves
Multi-product night shift showed mass FAIL: hardcodes on content/wiki/vendored trees, vault newest-first drift, harness-night-shift ACL, watchlist cross_review test mocks vs 3-tuple API.

## Why This Change Was Made
- P0 hardcode skips/allowlists + product --root; domain allows
- P0 watchlist: gate accepts legacy 2-tuple mocks; reinstall scripts
- P1 vault normalize epoch When fix; contract retry; group-write SUMMARY
- P2 daytime_readiness_subset + reinstall products

## User Impact
Fewer false night FAILs; daytime pre-check; vault logs writable.

## Evidence
- pytest 90; validate 5/5; smoke 2/2
- product hardcodes clean (substack, catalyxt, zk, watchlist, second-brain)
- check_dev_log_contract 8/8 OK

## Things that look bad but are actually fine
1. Skipping content/vault dirs does not weaken secret scan of src/
2. Path join for multi-user homes avoids literal /home/debian in source text
3. Daytime subset does not write vault (by design)
4. Normalize rewrites When only for epoch garbage
5. Product reinstall does not overwrite product_plugin smoke lists

## Cross-review
See .agents/artifacts/CROSS_REVIEW.md blockers=0
