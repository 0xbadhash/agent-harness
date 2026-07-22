# PR Draft — FSM glossary in ship-flow

**Date:** 2026-07-22  
**Task:** Define FSM = Finite State Machine where pipeline FSM is documented  
**Version target:** 1.3.3 (patch docs)

## What Problem This Solves

Operators and agents hit "pipeline FSM" / "ship FSM" without knowing the acronym. Ambiguity slows onboarding and causes wrong assumptions (product name vs process model).

## Why This Change Was Made

Explicit definition at the SoT (`docs/ship-flow.md`) with term table + light cross-links from README and overview.

## User Impact

Clearer mental model of ship phases; no runtime behavior change.

## Summary

- `docs/ship-flow.md`: FSM = Finite State Machine; phase/transition/gate table; kanban stages note  
- `docs/overview.md` / `README.md`: expand FSM once where scripts are listed  

## Evidence

- Commit `2bfc032` on main  
- Cross-review: `.agents/artifacts/CROSS_REVIEW.md` (blockers=0)  
- TDD: N/A (docs-only)

## Cross-review

See `.agents/artifacts/CROSS_REVIEW.md` — **Marker:** CROSS-REVIEW · blockers=0 majors=0 nits=1

## Things that look bad but are actually fine

1. **No unit tests for docs** — intentional; process gates still via validate/pr_validator.  
2. **Kanban stages listed in harness docs** — educational only; SoT for install FSM is pipeline.json.  
3. **Already on main before formal release** — commit landed early; this cycle tags the docs ship.  
4. **Patch not minor** — glossary only, no API surface.  
5. **Dirty normalize_vault_devlog left uncommitted** — separate change, not this release.
