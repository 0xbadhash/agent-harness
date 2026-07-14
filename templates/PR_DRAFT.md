# PR Draft: <version or title>

**Range:** `<tag>..HEAD` or `HEAD~N..HEAD`

## Summary

- …

## What Problem This Solves

[description]

What is broken, missing, or painful **before** this change? Be concrete (user-visible bug, agent friction, security gap, process hole). Not a restatement of the diff.

## Why This Change Was Made

[description]

Why **this** approach (and not alternatives)? Link to decision, spike, or constraint when useful. Keep rationale short.

## User Impact

[description]

Who notices, and how? (desk operator, agent session, ops, none if harness-only). Call out breaking changes or “no user-visible change.”

## Evidence

[description]

How we know it works: tests (red→green), live smoke, screenshots/logs, validator score, or `TDD N/A (docs-only)` with what was checked instead.

```text
red_cmd: <exact command that failed, if any>
green_cmd: <exact command that passed after fix>
# or: live: curl / puppeteer / health …
```

## Red-proof (optional Phase 2 — process honesty)

Same commands as Evidence when TDD applies. Not scored by pr_validator; required by team policy when enabled.

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
