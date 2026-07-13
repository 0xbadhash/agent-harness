# PR Draft: <version or title>

**Range:** `<tag>..HEAD` or `HEAD~N..HEAD`

## Summary

- …

## Red-proof (optional Phase 2 — process honesty)

Record the failing test command that was red **before** green. Not scored by pr_validator; required by team policy when enabled.

```text
red_cmd: <exact command that failed>
green_cmd: <exact command that passed after fix>
```

Or write: `TDD N/A (docs-only)`.

## Cross-review

See `.agents/artifacts/CROSS_REVIEW.md` or section below (marker **CROSS-REVIEW**).

## Test plan

- [ ] …

## Things that look bad but are actually fine

1. …
2. …
3. …

```yaml
things_that_look_bad_but_are_fine:
  - file: "…"
    concern: "…"
    why_fine: "…"
    validation: "…"
```
