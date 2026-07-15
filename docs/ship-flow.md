# Ship flow

## Pipeline FSM

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
1. `/execute_dev` — one task, TDD for code  
2. `/cross_review` — large diffs (record evidence)  
3. `/pr_review --validate` — score ≥ 95  
4. Product infra skill (optional) — hosts, TLS, deploy  
5. `/release_mgmt` — smoke from **product_plugin**, tag  
6. `/sync_docs` — docs + optional vault **release** entry  

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
| `.agents/artifacts/INFRA_RUNBOOK.md` | product infra skill |
| `RELEASE_RUNBOOK.md` | release_mgmt |
| Vault release block | sync_docs (`sync_vault_devlog.py` without `--note`) |
| Vault ad-hoc note | any task (`--note`; never `synced` in title) |

## Soft gates

- **Cross-review:** large diffs warn without evidence; optional `--strict-cross-review`  
  - Product paths come from `product_plugin.product_path_prefixes` (not hard-coded stack paths)
- **TDD:** process gate in execute_dev (red must fail before green)
- **Smoke:** `python3 scripts/product_smoke.py` reads plugin smoke[] at release
- **PR score `suite_green`:** green type/lint/test suite only — **not** red-first proof

## Related

- [TDD](tdd.md)  
- [Skills catalog](skills-catalog.md)  
