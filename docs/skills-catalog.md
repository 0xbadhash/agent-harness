# Skills catalog

Each skill is a folder with `SKILL.md` (YAML frontmatter + Markdown body).

**Full ship map (ASCII):** [ship-flow.md](ship-flow.md) — phases + skill branches  
**Detailed flow (Mermaid + SVG poster):** [ship-flow-detailed.md](ship-flow-detailed.md)  
**Prompt patterns → skills:** [prompt-patterns.md](prompt-patterns.md)  
(`/code_review`, `/cross_review`, `/behavior_validator`, `/vps_infra_ops` when required, `NEXT_SKILL=`).

**CODER mode** (C=Compute, O=Organize, D=Display, E=Engineer, R=Reason): teaching labels only — not pipeline phases. Session pack: `python3 scripts/session_context.py --write`.

## User-invoked (ship) — `config/ship_skills.txt`

| Skill | Mode | When to fire | Does |
|-------|------|--------------|------|
| `spec` | R/O | **Start of every feature** | Constitution → **grill-me** → draft → clarify → AC (+ plan/tickets); optional `--roadmap-from-gap` (ex-plan_backend). Phase stays `init`. |
| `execute_dev` | E/C | Building one task | TDD, implement, validate; handoff → `ready_for_review` |
| `code_review` | E/R | After execute_dev (non-prose) | P0-first closeout |
| `cross_review` | R | Large / multi-persona | Multi-persona + obsolete scan (scoped) |
| `behavior_validator` | C/E | Runtime surface | Source-blind contract check |
| `pr_review` | C | Scoring | Deterministic rubric; sets `approved`/`blocked` |
| `release_mgmt` | E/C | Shipping | Smoke, version, tag, `shipped` |
| `sync_docs` | O/D | After ship | Repo (+ optional vault) stamps → `init` |
| `night_shift` | C/O | Overnight readiness | Gates + smoke + suite orchestration; **parallel products** (`--jobs`); vault TODO; no auto-ship; **no ZAP crawl** |
| `sweep` | C/E | Hygiene | Drift, skills audit, **primary obsolete-scan** |
| `handoff` | D/O | Switch agent | Continuity prompt |
| `plan_review` | R | After `/spec` when `**Plan:**` linked | Pre-code plan review → `PLAN_REVIEW.md` (`NEXT_SKILL` routes; skip if no Plan) |

## Optional (not in ship_skills) — `config/optional_skills.txt`

Installed if present; **not** verify-required. Router may suggest on large ships only.

| Skill | Mode | When to fire | Does |
|-------|------|--------------|------|
| `session_viewer` | D | Debug session log | JSONL/text → local HTML |
| `agent_transcript` | D/O | Optional PR provenance | Sanitized markdown; ask user first |
| `qa_campaign` | E/C | After sync_docs on **large** (or `--force-qa`) | Deep QA — honest skip on small ships |
| `retrospect` | O/R | After ship / night fail | Learning loop (manual) |
| `audit_harness` | C | Process audit | Scorecard + policy-gap (manual) |

## Removed (do not install)

Listed in `config/removed_portable_skills.txt` (product `--delete-stale-skills`):

| Former skill | Replaced by |
|--------------|-------------|
| `feedback` | Session notes / vault dev-log / `/retrospect` |
| `plan_backend` | `/spec --roadmap-from-gap` |
| `audit_repo` | `/sweep` (hygiene) + `/audit_harness` (policy gap) |
| `test_automation` | `/night_shift` suite section + product_smoke / validate |

## Product-only skills

Live **only** in the product repo under `.agents/skills/<name>/`.  
Examples: `vps_infra_ops`, deploy, cloud topology.  
**Never** copy product hostnames into this harness repo.

## Key scripts (not skills)

| Script | Role |
|--------|------|
| `scripts/next_skill.py` | `NEXT_SKILL=…` handoff |
| `scripts/spec_gate.py` + `check_spec_grill.py` | Spec + grill evidence |
| `scripts/pipeline_state.py` | FSM |
| `scripts/pr_validator.py` | PR score |
| `scripts/night_shift_readiness.py` | Night bar |
| `scripts/session_viewer.py` / `agent_transcript.py` | Optional helpers |

## Install + verify

```bash
python3 scripts/verify_skills.py          # ship_skills presence
bash scripts/bootstrap_check.sh
# prune deleted portable skills from a product:
./install_into_product.sh /path/to/product --delete-stale-skills
```

## Related

- [Writing skills](writing-skills.md)  
- [Ship flow](ship-flow.md)  
- [Start a feature](start-a-feature.md)  
- [Night shift](night-shift.md)  
