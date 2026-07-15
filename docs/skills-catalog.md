# Skills catalog

Each skill is a folder with `SKILL.md` (YAML frontmatter + Markdown body).

## User-invoked (ship)

| Skill | When to fire | Does |
|-------|--------------|------|
| `spec` | Before coding a new idea | Interview/synthesize → `.agents/specs/` + roadmap OPEN item (does not advance pipeline) |
| `execute_dev` | Building one task | TDD, implement, validate, handoff → `ready_for_review` |
| `cross_review` | Before score on non-trivial diffs | Multi-persona review + evidence file |
| `pr_review` | Scoring a ready change | Deterministic rubric; soft cross-review warn |
| `release_mgmt` | Shipping | Smoke (plugin), version, tag, `shipped` |
| `sync_docs` | After ship | Drift/docs/vault release entry → `init` |

## Support

| Skill | When to fire | Does |
|-------|--------------|------|
| `sweep` | Hygiene pass | Status, drift, skills audit |
| `feedback` | End of session | Harness feedback log |
| `audit_repo` | Policy gaps | Gap analysis doc |
| `plan_backend` | After audit | Roadmap structure (product fills content) |
| `test_automation` | Suite orchestration | Run/scaffold tests |

## Product-only skills

Live **only** in the product repo under `.agents/skills/<name>/`.  
Examples: deploy, cloud topology, app-specific ops.  
**Never** copy product hostnames into this harness repo.

## Description field (routing)

The YAML `description` is the agent’s **load trigger**. Front-load:

- What the skill does  
- When it should fire  
- When it must **not** fire  

Vague descriptions → wrong skill loads → wasted context.

## Related

- [Writing skills](writing-skills.md)  
- [Ship flow](ship-flow.md)  
