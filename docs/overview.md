# Overview

## Problem

Coding agents are capable improvisers. Without a harness they:

- Re-ask for process every session  
- Skip tests, then invent them after  
- Mix one product’s conventions into another  
- Ship without a deterministic gate  

## Solution

**agent-harness** is a portable kit:

1. **Skills** — pull-loaded workflows (`SKILL.md`)  
2. **Scripts** — push-button gates (validate, score, pipeline FSM)  
3. **Policy** — short always-on rules  
4. **Product plugin** — *your* stack and smoke commands  

Install into a product → develop that product → leave other products alone.

## Boundaries

| Belongs in harness | Belongs in product |
|--------------------|--------------------|
| Ship sequence | Domain code |
| TDD / review skills | Language, framework, UI |
| Pipeline phases | Roadmap / backlog content |
| Generic vault *format* | Vault *project path* & labels |
| Soft cross-review gate | Hostnames, deploy, infra topology |

## Progressive disclosure

Same idea as Agent Skills tiers:

| Tier | What loads | Cost |
|------|------------|------|
| 1 | Skill name + description | Tiny |
| 2 | Full `SKILL.md` when invoked | Medium |
| 3 | Scripts / templates when the skill runs | Only if needed |

Keep skill bodies short. Put long checklists in `docs/` and link them.

## Failure modes → skills

| Failure mode | Skill response |
|--------------|----------------|
| Built the wrong thing | `/spec` (interview + acceptance) then single-task `/execute_dev` |
| Untested code | **TDD** gate in `/execute_dev` |
| “Looks fine” ship | `/pr_review` score + `/cross_review` |
| Docs / vault drift | `/sync_docs` + Option A note vs release entries |
| Entropy | `/sweep`, architecture notes in product |

## Related

- [Bootstrap](bootstrap.md)  
- [Product plugin](product-plugin.md)  
- [Ship flow](ship-flow.md)  
