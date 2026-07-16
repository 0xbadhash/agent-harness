# Skills catalog

Each skill is a folder with `SKILL.md` (YAML frontmatter + Markdown body).

## User-invoked (ship)

| Skill | When to fire | Does |
|-------|--------------|------|
| `spec` | Before coding a new idea | Constitution → interview → draft → clarify → `.agents/specs/` (+ optional plan/tickets) + roadmap OPEN (no pipeline advance) |
| `execute_dev` | Building one task | TDD, implement, validate, handoff → `ready_for_review` |
| `cross_review` | Before score on non-trivial diffs | Multi-persona review + scoped obsolete/cleanup scan + evidence file |
| `pr_review` | Scoring a ready change | Deterministic rubric; soft cross-review warn |
| `release_mgmt` | Shipping | Smoke (plugin), version, tag, `shipped` |
| `sync_docs` | After ship | Full repo+vault doc sync (workflow, mirrors, wiki, release log) → `init` |

## Support

| Skill | When to fire | Does |
|-------|--------------|------|
| `anti_slop_design` | Any UI/UX/frontend design or polish | pols.dev anti-slop law: confirm → build → point-by-point pre-ship audit ([slop.md](https://pols.dev/slop.md)) |
| `sweep` | Hygiene pass | Status, drift, skills audit, whole-repo obsolete/cleanup (evidence only) |
| `feedback` | End of session | Harness feedback log |
| `audit_repo` | Policy gaps | Gap analysis + whole-repo obsolete/cleanup (evidence only) |
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
