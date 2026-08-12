# RELEASE_RUNBOOK — agent-harness v1.4.28

**Date:** 2026-08-12  
**Score:** 100  
**Phase:** shipped

## Smoke

| Step | Result |
|------|--------|
| hardcodes | pass |
| smoke_unit | pass (208 tests incl. tier_abc) |

## Evidence

- hard_gates: ok, 10 AC mapped
- pr_validator score 100
- Spec: docs/specs/2026-08-12-tier-abc-best-of-harness.md

## Rollback

```bash
git checkout v1.4.27
# portfolio: reinstall from previous tag if needed
```

## §9 things that look bad but are fine

1. C15 multi-agent not built — NON_GOAL  
2. SBOM warn-only  
3. protect_sot_merge report-only  
4. GitHub daytime best-effort  
5. recovery resumable not proven-durable  
