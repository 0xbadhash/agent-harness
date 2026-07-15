# Provenance — portable `/spec`

What we borrowed and what we deliberately dropped.

## Alex Finn — Finn Loop `/spec`

**Kept:** idea string → interview until clear → agent-grabbable work item; multi-issue when complex; front door of spec → build → review.

**Optional / not required:** Linear (flag only), always-on multi-session factory, Slack merge emoji, Vercel sandbox (product-only skills if needed).

## Matt Pocock engineering skills

| Skill | Borrowed |
|-------|----------|
| grill / grill-me | One Q at a time; recommended answer; look up facts |
| to-spec | PRD template; domain language; seams; no path spam |
| to-tickets | Optional vertical slices + blockers under `.agents/specs/…/tickets/` |
| implement / tdd / code-review | Hand off to `/execute_dev`, `/cross_review`, `/pr_review` |

## Fable-style autonomous workflows

Not a monetization content pack. Constraints only:

1. Complete written brief before long unattended `/execute_dev`
2. Artifact-first handoff (files + roadmap OPEN item)
3. Explore repo before asking
4. Batchable tickets when work exceeds one context window

## Harness fit

```text
/spec → /execute_dev → /cross_review → /pr_review → /release_mgmt → /sync_docs
```

- Does **not** mutate `pipeline.json`
- Roadmap OPEN + acceptance criteria feed `/execute_dev` (`SPEC MISSING` guard)
- Portable: ships in this repo under `skills/spec/`; install copies to product `.agents/skills/spec/`
