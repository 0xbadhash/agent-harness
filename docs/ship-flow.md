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

1. `/execute_dev` — one task, TDD for code  
2. `/cross_review` — large diffs (record evidence)  
3. `/pr_review --validate` — score ≥ 95  
4. Product infra skill (optional) — hosts, TLS, deploy  
5. `/release_mgmt` — smoke from **product_plugin**, tag  
6. `/sync_docs` — docs + optional vault **release** entry  

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
- **TDD:** process gate in execute_dev (red must fail before green)

## Related

- [TDD](tdd.md)  
- [Skills catalog](skills-catalog.md)  
