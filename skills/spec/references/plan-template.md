# Technical plan template (`/spec --plan`)

Write to `.agents/specs/<YYYY-MM-DD>-<slug>-plan.md`.  
This is the **how**. The companion spec file is the **what/why**.

---

```markdown
# Plan: <Title>

- **Spec:** `.agents/specs/<YYYY-MM-DD>-<slug>.md`
- **Product:** <product_id>
- **Created:** <ISO date>
- **Status:** ready-for-agent

## Stack & constraints

From `product_plugin.yaml` and constitution — only overrides here if user required them:

- Languages / package manager / runners
- Hard constraints (frontend-only, no new backend, etc.)

## Approach

Short prose: how we implement the acceptance criteria.

## Architecture decisions

- Modules / packages / routes
- Data flow (if any)
- Integration points (EmailJS, APIs, …)
- Explicit non-decisions (deferred)

## File / surface map (indicative)

Prefer areas over brittle line numbers:

| Area | Change |
|------|--------|
| … | … |

## Implementation sequence

Ordered steps that map cleanly to `/execute_dev` tickets if split:

1. …
2. …

## Testing plan

- Seams
- Smoke from plugin
- Manual paths
- TDD notes for `/execute_dev`

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| … | … |

## Open questions

None — or list residual (should be empty after clarify).
```
