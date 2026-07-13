# Product plugin

**File:** `.agents/product_plugin.yaml` (in the **product** repo)

This is the only required product-specific config for the harness.  
**Stack is chosen here—not inside skills.**

## Full example (stack-agnostic)

```yaml
product_id: example-api
product_name: Example API
repo_root: .

stack:
  languages: [go]
  package_manager: go
  test_runners: [go test]
  app_layout: cmd/, internal/

product_roadmap: ROADMAP.md
harness_backlog: .agents/BACKLOG.md

smoke:
  - name: unit
    cmd: ["go", "test", "./..."]
    cwd: .
  - name: build
    cmd: ["go", "build", "./..."]
    cwd: .

vault:
  root_env: PRODUCT_VAULT_ROOT
  default_root: ""          # empty = vault optional / skip
  dev_log_rel: 01-Projects/example-api/dev-log.md
  project_label: example-api

product_path_prefixes:
  - cmd/
  - internal/
  - pkg/

domain_review_hints:
  - API contracts stable
  - no secret leakage
  - errors observable

product_skills:
  - deploy   # optional names of product-only skills
```

## Field reference

| Field | Required | Description |
|-------|----------|-------------|
| `product_id` | yes | Short slug |
| `product_name` | yes | Human name |
| `stack` | recommended | Free-form metadata for agents (not executed) |
| `smoke` | yes for release | List of `{name, cmd[], cwd?}` — **executed** at release |
| `product_path_prefixes` | recommended | Paths that count as product code for large-diff heuristics |
| `vault` | no | Second-brain / release note location |
| `domain_review_hints` | no | Domain persona cues for `/cross_review` |
| `product_skills` | no | Names of skills that live only in the product |

## Rules

1. **No framework defaults in the harness** — if smoke is empty, `/release_mgmt` must refuse or skip with explicit policy.  
2. **`cmd` is argv arrays** — no shell injection; no product secrets in the file.  
3. **`stack` is documentation for the agent** — change stack by editing the plugin, not by forking skills.  
4. **One product plugin per product repo** — never point two products at the same `pipeline.json` state.

## Bootstrap checklist

- [ ] `stack.languages` set  
- [ ] At least one smoke command that fails if the app is broken  
- [ ] `product_path_prefixes` match real source roots  
- [ ] Vault filled or clearly empty/optional  
- [ ] Product-only skills listed if any  

## Related

- [Bootstrap](bootstrap.md)  
- [Ship flow](ship-flow.md)  
