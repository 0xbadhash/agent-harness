# Spec template (`/spec`)

Write to `.agents/specs/<YYYY-MM-DD>-<slug>.md`. Fill every section; use `N/A` only with a reason.

---

```markdown
# <Title>

- **Product:** <product_id from product_plugin>
- **Created:** <ISO date>
- **Status:** ready-for-agent
- **Priority:** P0 | P1 | P2
- **Roadmap:** <product_plugin.product_roadmap path> → Open work
- **Tracker:** local | Linear <url> | GitHub <url>

## Problem Statement

The problem from the **user/operator** perspective — not the implementer’s.

## Solution

What they experience when it works — still user-facing language.

## User Stories

Numbered, extensive enough for the slice:

1. As a <actor>, I want <feature>, so that <benefit>

## Implementation Decisions

- Modules / surfaces — names and behavior (avoid fragile line-level paths)
- Stack constraints from `product_plugin.yaml` → `stack`
- Explicit non-goals
- Contracts (API/schema) only if the product has them

## Testing Decisions

- External behavior, not internals
- Seams (highest useful public contract)
- Commands: product `smoke[]` from plugin + any manual path
- Prior art in the codebase
- Docs-only? → TDD N/A for `/execute_dev`

## Acceptance Criteria

Checkable pass/fail only:

- [ ] …
- [ ] …
- [ ] Product smoke commands succeed
- [ ] No secrets committed

## Out of Scope

Bullet list. Protects `/execute_dev` from scope creep.

## Further Notes

Risks, interview decisions, links.

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
