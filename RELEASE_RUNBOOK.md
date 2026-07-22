# Release runbook — agent-harness v1.3.3

**Date:** 2026-07-22  
**Version:** 1.3.3  
**Scope:** Docs — define FSM as Finite State Machine in ship-flow  
**Prior:** 1.3.2  
**Commit:** 2bfc032 (+ this release metadata)

## Smoke

| Check | Result |
|-------|--------|
| `python3 scripts/validate.py full` | PASS (see CI/local log) |
| `python3 scripts/product_smoke.py --root .` | PASS / warn if empty smoke |
| Cross-review | blockers=0 (`.agents/artifacts/CROSS_REVIEW.md`) |
| PR score | 100 → approved |

## Infra

None required (docs-only; no host topology change).

## Rollback

```bash
git checkout v1.3.2
# or revert docs commit 2bfc032
```

## Things that look bad but are actually fine

1. **Docs-only version bump** — operators need a tagged SoT for "what is FSM".  
2. **No product reinstall required for acronym text** — optional `install_into_product` to refresh mirrored docs.  
3. **Main already had the commit before tag** — normal for private harness docs ships.  
4. **normalize_vault_devlog dirty left out** — not part of 1.3.3.  
5. **Kanban stages mentioned** — educational; install FSM remains pipeline.json.
