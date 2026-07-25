# Ship flow

## Pipeline FSM

**FSM** means **Finite State Machine**: a fixed set of **phases (states)** and allowed **transitions**. The ship pipeline is an FSM so agents cannot invent arbitrary “we’re done” paths — each skill only advances when the current phase and gates allow it.

| Term | Meaning here |
|------|----------------|
| **FSM** | Finite State Machine (not a product name or acronym for something else) |
| **Phase / state** | One of: `init` → `ready_for_review` → `approved` \| `blocked` → `shipped` → `init` |
| **Transition** | Moving to the next phase via `scripts/pipeline_state.py` only |
| **Gate** | Deterministic check before a transition (e.g. PR score ≥ 95, TDD evidence) |

Related (product vaults / second-brain kanban): a **card-level ship FSM** may use stages like `spec` → `execute_dev` → `cross_review` → `pr_review` → `release` → `sync_docs` → `done`. That is the same idea (states + gates); harness SoT for **product install** pipeline state is still `.agents/state/pipeline.json` below.

```text
init
  │
  ▼
ready_for_review  ──▶  blocked ──(fix)──▶ ready_for_review
  │
  ▼
approved
  │
  ▼
shipped
  │
  ▼
init
```

State file (per product): `.agents/state/pipeline.json`  
Mutations: `scripts/pipeline_state.py` only (atomic).

## Phase ownership

| Phase | Who advances | Skill |
|-------|--------------|--------|
| init | start work | — |
| ready_for_review | implementer | `/execute_dev` |
| approved / blocked | reviewer | `/pr_review --validate` |
| shipped | releaser | `/release_mgmt` (after product infra checks if any) |
| init (again) | docs | `/sync_docs` |

## Recommended order

0. `/spec` — constitution + interview + **clarify**; write `.agents/specs/` (+ optional `-plan.md` / tickets) + roadmap OPEN (pipeline unchanged)  
1. `/execute_dev` — one task, TDD for code (scope governor: no silent expansion)  
2. **Print `NEXT_SKILL=…`** via `scripts/next_skill.py --after execute_dev` (usually `/code_review`)  
3. `/code_review` — required for non-prose; then **`NEXT_SKILL=…`** again  
4. `/cross_review` and/or `/behavior_validator` — **only if** `NEXT_SKILL` says so  
5. **Smoke / validate** — behavior ≠ source  
6. `/pr_review --validate` — score ≥ 95 → phase `approved`  
7. Product infra skill (optional) — hosts, TLS, deploy  
8. `/release_mgmt` — smoke from **product_plugin**, tag  
9. `/sync_docs` — docs + optional vault **release** entry  

**Always parse one line:** `NEXT_SKILL=/skill …` — do not invent the next step.

### Side skills (not ship phases)

| Skill | When |
|-------|------|
| `/handoff` | Switch agent/session |
| `/session_viewer` | HTML view of a local session log |
| `/agent_transcript` | Sanitized transcript for PR body (ask user first) |

### Review helpers (scripts)

| Script | Role |
|--------|------|
| `scripts/next_skill.py` | **Single-line handoff** `NEXT_SKILL=…` after each step |
| `scripts/review_scope.py` | Baseline files/LOC; `prose_only` / `skip_heavy_review` |
| `scripts/check_secrets_diff.py` | Diff-scoped secret scan (gitleaks/trufflehog or regex) |
| `scripts/session_viewer.py` | JSONL/text → HTML |
| `scripts/agent_transcript.py` | find/render sanitized markdown |
| `scripts/cross_review_gate.py` | Soft large-diff evidence warn |
| `scripts/pr_validator.py` | Deterministic score + pipeline phase |

## PR_DRAFT narrative (template)

Implementers fill `PR_DRAFT.md` from `templates/PR_DRAFT.md` before `/pr_review`:

| Section | Intent |
|---------|--------|
| **What Problem This Solves** | Pain / bug / gap before the change |
| **Why This Change Was Made** | Rationale and rejected alternatives |
| **User Impact** | Who notices (operator, agent, ops, none) |
| **Evidence** | Tests, live smoke, validator — how we know it works |
| Red-proof / Cross-review / §9 | Existing process gates |

## Artifacts

| Artifact | Owner |
|----------|--------|
| `PR_DRAFT.md` | pr_review / implementer |
| `.agents/artifacts/CROSS_REVIEW.md` | cross_review |
| `.agents/artifacts/CODE_REVIEW.md` | code_review (optional) |
| `.agents/artifacts/INFRA_RUNBOOK.md` | product infra skill |
| `RELEASE_RUNBOOK.md` | release_mgmt |
| Vault release block | sync_docs (`sync_vault_devlog.py` without `--note`) — shape: **[dev-log.md](dev-log.md)** |
| Vault ad-hoc note | any task (`--note`; never `synced` in title) — same Option A standard |

## Validate gates (`validate.py full`)

| Gate | When |
|------|------|
| compliance_engine (type/lint/test) | full / compliance |
| check_hardcodes | full / hygiene |
| check_repo_hygiene | full / hygiene |
| check_module_coverage | full / hygiene |
| **check_dev_log_contract** | full / hygiene **if vault present** (this product’s `01-Projects/<label>/dev-log.md`) |

See `docs/dev-log.md`. Overnight multi-product job still normalizes + checks **all** logs.

## Soft gates

- **Cross-review:** large diffs warn without evidence; optional `--strict-cross-review`  
  - Product paths come from `product_plugin.product_path_prefixes` (not hard-coded stack paths)
- **TDD:** process gate in execute_dev (red must fail before green)
- **Smoke:** `python3 scripts/product_smoke.py` reads plugin smoke[] at release
- **PR score `suite_green`:** green type/lint/test suite only — **not** red-first proof

## Off-pipeline: night readiness (`/night_shift`)

**Not** a ship FSM phase. Overnight (or on-demand) **readiness** so the next `/execute_dev` can start on green surfaces.

- Does **not** advance `pipeline.json`  
- Does **not** release or tag  
- Writes reports + optional vault TODO only  

Full ops doc: **[night-shift.md](night-shift.md)**.

## Related

- [TDD](tdd.md)  
- [Night shift](night-shift.md)  
- [Skills catalog](skills-catalog.md)  
