# Provenance — portable `/spec`

## Evolution (v1.2)

Extended without requiring [Spec Kit](https://github.com/github/spec-kit) install:

| Addition | Spec Kit analogue | Harness path |
|----------|-------------------|--------------|
| Constitution read | `/speckit.constitution` | `.agents/CONSTITUTION.md` or policy |
| Clarify pass | `/speckit.clarify` | `## Clarifications` + checklist |
| Optional plan file | `/speckit.plan` | `.agents/specs/…-plan.md` |
| Tickets | `/speckit.tasks` | `--tickets` under `.agents/specs/…/tickets/` |
| Optional Spec Kit detect | full SDD toolkit | `references/speckit-bridge.md` only if `.specify/` exists |

Ship remains harness-owned: `/execute_dev` → `/cross_review` → `/pr_review` → `/release_mgmt` → `/sync_docs`.

## Earlier sources

- **Alex Finn** — idea → interview → agent-grabbable work item  
- **Matt Pocock** — grill, to-spec template, to-tickets  
- **Fable-style** — complete brief before unattended implement  
