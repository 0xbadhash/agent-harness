# Spec template (`/spec`)

Write to `.agents/specs/<YYYY-MM-DD>-<slug>.md`.  
**What / why** only. Technical **how** goes in optional `-plan.md` when using `--plan`.

**Grill-me is mandatory** (see `grill-me-checklist.md`). Do not mark `ready-for-agent` without `## Grill-me`.

---

```markdown
# <Title>

- **Product:** <product_id from product_plugin>
- **Created:** <ISO date>
- **Status:** draft | ready-for-agent | rejected
- **Priority:** P0 | P1 | P2
- **Roadmap:** <product_plugin.product_roadmap path> → Open work
- **Plan:** `.agents/specs/<…>-plan.md` | none
- **Tracker:** local | Linear <url> | GitHub <url>
- **Constitution:** .agents/CONSTITUTION.md | AGENTS.md | policy defaults
- **Grill-me:** complete | spike-skipped

## Problem Statement

The problem from the **user/operator** perspective — not the implementer’s.

## Solution

What they experience when it works — still user-facing language.

## User Stories

Numbered, extensive enough for the slice:

1. As a <actor>, I want <feature>, so that <benefit>

## Implementation Decisions

Light-touch only (surfaces, non-goals). Prefer `-plan.md` for stack/architecture when non-trivial.

- Modules / surfaces — names and behavior
- Explicit non-goals that affect the experience
- Pointers to constitution constraints that apply

## Testing Decisions

- External behavior, not internals
- Seams (highest useful public contract)
- Commands: product `smoke[]` + any manual path
- Docs-only? → TDD N/A for `/execute_dev`

## Acceptance Criteria

Checkable pass/fail only:

- [ ] …
- [ ] …
- [ ] Product smoke commands succeed
- [ ] No secrets committed

## Out of Scope

Bullet list. Protects `/execute_dev` from scope creep.

## Grill-me

**Status:** complete | spike-skipped
**Date:** <ISO date>

### G1 Outcome
- Q: …?
  - A: …

### G2 Non-goal / kill
- Q: …?
  - A: …

### G3 Wrong product
- Q: …?
  - A: …

### G4 Cheapest alternative
- Q: …?
  - A: …

### G5 Abuse / failure
- Q: …?
  - A: …

### G6 Verify
- Q: …?
  - A: …

### G7 Priority
- Q: …?
  - A: …

(If spike-skipped: omit G* and put **Reason:** ≥20 chars under Status.)

## Clarifications

### <ISO date>
- Q: …
  - A: …

## Further Notes

Risks, constitution tensions, links.

## Handoff

- Next: `/execute_dev` (one sub-task; TDD when code changes)
- Then: `/cross_review` (if large) → `/pr_review` → `/release_mgmt` → `/sync_docs`
```

---

## Ticket file template (`--tickets`)

`.agents/specs/<slug>/tickets/01-<name>.md`:

```markdown
# 01 — <Ticket title>

**What to build:** end-to-end behaviour from the user’s perspective.

**Blocked by:** None — can start immediately | 02 — …

**Status:** ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2
```
