# Skills catalog

Each skill is a folder with `SKILL.md` (YAML frontmatter + Markdown body).

**Full ship map (ASCII):** [ship-flow.md](ship-flow.md) — phases + skill branches  
(`/code_review`, `/cross_review`, `/behavior_validator`, `/vps_infra_ops` when required, `NEXT_SKILL=`).

## User-invoked (ship)

| Skill | When to fire | Does |
|-------|--------------|------|
| `spec` | **Start of every feature** (not optional for code ships) | Constitution → interview → draft → clarify → checkable AC in `.agents/specs/` (+ plan/tickets) + roadmap OPEN. Phase stays `init`, but hard gates / `spec_gate` require Spec path or waiver. Guide: [start-a-feature.md](start-a-feature.md) |
| `execute_dev` | Building one task | TDD, implement, validate; mandatory `/code_review` closeout for non-prose; handoff → `ready_for_review`; prints `NEXT_SKILL=` |
| `code_review` | After execute_dev (non-prose code) | P0-first closeout; required unless prose-only; secrets + scope; prints `NEXT_SKILL=` |
| `cross_review` | When `NEXT_SKILL=/cross_review` | Multi-persona + obsolete scan; P0-first; then `NEXT_SKILL=` |
| `behavior_validator` | When `NEXT_SKILL=/behavior_validator` | Source-blind contract check; then `NEXT_SKILL=/pr_review --validate` |
| `pr_review` | Scoring a ready change | Deterministic rubric; soft cross-review; secrets; smoke reminder; **only** skill that sets `approved`/`blocked` |
| `vps_infra_ops` | After `approved`, **only if required** | **Product-owned** (not in portable install). `--verify` → `INFRA_RUNBOOK.md`; phase stays `approved`; then `NEXT_SKILL=/release_mgmt` |
| `release_mgmt` | Shipping | Smoke (plugin), version, tag, `shipped` (expects infra PASS when required) |
| `sync_docs` | After ship | Full repo+vault doc sync → `init` |
| `qa_campaign` | After full FSM / **large** release | Deep multi-layer QA + bug hunt; suggested after `/sync_docs` only when diff is large (`--force-qa` to always) |
| `retrospect` | After ship or night_shift fail | Learning loop → `RETRO.md` backlog items; not a phase |

Ship-chain manifest (must install): `config/ship_skills.txt`.

## Support (not ship phases)

| Skill | When to fire | Does |
|-------|--------------|------|
| `handoff` | Switch agent / delegate | Clipboard-ready handoff prompt for a fresh agent (P2) |
| `session_viewer` | Inspect a session log | JSONL/text → local HTML (P3) |
| `agent_transcript` | Optional PR provenance | Sanitized markdown; ask user before PR insert (P3) |
| `night_shift` | Overnight / on-demand readiness | Gates (matrix, smoke, coverage, optional live); vault TODO + night-shift-log; multi-product timer 03:15 HKT; **no** auto-ship — [night-shift.md](night-shift.md) |
| `sweep` | Hygiene pass | Status, drift, skills audit, whole-repo obsolete/cleanup (evidence only) |
| `feedback` | End of session | Harness feedback log |
| `audit_repo` | Policy gaps | Gap analysis + whole-repo obsolete/cleanup (evidence only) |
| `audit_harness` | Harness self-audit | Policy / install health of the harness kit |
| `plan_backend` | After audit | Roadmap structure (product fills content) |
| `test_automation` | Suite orchestration | Run/scaffold tests |

## Product-only skills

Live **only** in the product repo under `.agents/skills/<name>/`.  
Examples: `vps_infra_ops`, deploy, cloud topology, app-specific ops.  
**Never** copy product hostnames into this harness repo.

## Key scripts (not skills)

| Script | Role |
|--------|------|
| `scripts/next_skill.py` | Single-line `NEXT_SKILL=…` after ship steps |
| `scripts/smoke_unit.sh` | Portable unit smoke (no nested `bash -c`) |
| `scripts/daytime_readiness_subset.py` | Daytime hardcodes + validate + smoke (pre-night) |
| `scripts/ensure_vault_group_write.py` | Vault ACL/group-write for night_shift logs |
| `scripts/vault_fs.py` | Group-friendly vault file writes |
| `scripts/check_hardcodes.py` | Zero-tolerance hardcodes (with content/vendored skips) |
| `scripts/pipeline_state.py` | FSM phase get/set |
| `scripts/pr_validator.py` | Deterministic PR score |

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
- [Night shift](night-shift.md)  
