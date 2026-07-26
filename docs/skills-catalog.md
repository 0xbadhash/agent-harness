# Skills catalog

Each skill is a folder with `SKILL.md` (YAML frontmatter + Markdown body).

**Full ship map (ASCII):** [ship-flow.md](ship-flow.md) — phases + skill branches (`/code_review`, `/cross_review`, `/behavior_validator`, `/vps_infra_ops` when required, `NEXT_SKILL=`).

## User-invoked (ship)

| Skill | When to fire | Does |
|-------|--------------|------|
| `spec` | Before coding a new idea | Constitution → interview → draft → clarify → `.agents/specs/` (+ optional plan/tickets) + roadmap OPEN (no pipeline advance) |
| `execute_dev` | Building one task | TDD, implement, validate, handoff → `ready_for_review` |
| `code_review` | After execute_dev (non-prose code) | P0-first closeout; required unless prose-only; prints `NEXT_SKILL=` |
| `cross_review` | When `NEXT_SKILL=/cross_review` | Multi-persona + obsolete scan; P0-first; then `NEXT_SKILL=` |
| `behavior_validator` | When `NEXT_SKILL=/behavior_validator` | Source-blind contract check; then `NEXT_SKILL=/pr_review --validate` |
| `pr_review` | Scoring a ready change | Deterministic rubric; soft cross-review; secrets; smoke reminder |
| `vps_infra_ops` | After `approved`, **only if required** | Product-owned; `--verify` → `INFRA_RUNBOOK.md`; phase stays `approved`; then `NEXT_SKILL=/release_mgmt`. **Not** installed by portable harness — only when the product provides the skill or plugin flags infra required |
| `release_mgmt` | Shipping | Smoke (plugin), version, tag, `shipped` (expects infra PASS when required) |
| `sync_docs` | After ship | Full repo+vault doc sync (workflow, mirrors, wiki, release log) → `init` |

## Support

| Skill | When to fire | Does |
|-------|--------------|------|
| `handoff` | Switch agent / delegate | Clipboard-ready handoff prompt for a fresh agent |
| `session_viewer` | Inspect a session log | JSONL/text → local HTML |
| `agent_transcript` | Optional PR provenance | Sanitized markdown; ask user before PR insert |
| `anti_slop_design` | Any UI/UX/frontend design or polish | pols.dev anti-slop law: confirm → build → point-by-point pre-ship audit ([slop.md](https://pols.dev/slop.md)) |
| `sweep` | Hygiene pass | Status, drift, skills audit, whole-repo obsolete/cleanup (evidence only) |
| `night_shift` | Overnight / on-demand readiness | Gates (matrix, smoke, coverage, optional live); vault TODO + night-shift-log; multi-product timer 03:15 HKT; **no** auto-ship — [docs/night-shift.md](night-shift.md) |
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

## Install + verify

After `install_into_product.sh`, ship-chain skills are listed in `config/ship_skills.txt` (copied to `.agents/policy/ship_skills.txt`).

```bash
python3 scripts/verify_skills.py          # frontmatter + ship-chain presence
bash scripts/bootstrap_check.sh           # files + pipeline + next_skill smoke
```

Any LLM: [llm-bootstrap.md](llm-bootstrap.md).

## Related

- [Writing skills](writing-skills.md)  
- [Ship flow](ship-flow.md)  
- [LLM bootstrap](llm-bootstrap.md)  
