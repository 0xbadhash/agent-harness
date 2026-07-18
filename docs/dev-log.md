# Vault `dev-log.md` standard (Option A)

**SoT:** this document + `scripts/sync_vault_devlog.py` (agent-harness).  
Products receive the writer via `install_into_product.sh`. Do **not** invent a second format in product repos.

**Path (every product):**

```text
$PRODUCT_VAULT_ROOT/01-Projects/<project_label>/dev-log.md
```

`<project_label>` comes from `.agents/product_plugin.yaml` → `vault.project_label` (fallback `product_id`).

---

## File layout

```markdown
# <project_label> dev log

Newest first. Times: UTC + HKT. Writers: harness `sync_vault_devlog` only.

Agent-appended development notes (<project_label> → optional knowledge vault).

## YYYY-MM-DD — <title or vX.Y.Z synced>

- **When:** YYYY-MM-DD HH:MM UTC · YYYY-MM-DD HH:MM HKT
- **Kind:** release | note
- …
```

| Rule | Spec |
|------|------|
| **Order** | **Newest first** (entries prepended after the file header) |
| **Clock** | Every new entry has **When:** with **UTC · HKT** |
| **Writers** | Only `scripts/sync_vault_devlog.py` (or `/sync_docs` → same script). No raw `cat >>` |
| **Header** | Stable `# <label> dev log` + “Newest first…” blurb; never a freeform title alone |

Decisions that need a durable record go in `01-Projects/<label>/decisions.md` (separate file), not only in dev-log.

---

## Two entry kinds (Option A)

### 1. Release (after `/sync_docs` only)

**Header shape:**

```markdown
## YYYY-MM-DD — vX.Y.Z synced
```

**Required fields (order):**

| Field | Example |
|-------|---------|
| When | `- **When:** 2026-07-18 07:13 UTC · 2026-07-18 15:13 HKT` |
| Kind | `- **Kind:** release` |
| Release | `- **Release:** \`v2.3.39\` (tag \`v2.3.39\`)` |
| Scope | `- **Scope:** …` |
| Tests | `- **Tests:** …` |
| Next (Shaping) | `- **Next (Shaping):** …` |
| Pipeline | `- **Pipeline:** shipped → init` |
| Repo | `- **Repo:** \`/path/to/product\`` |
| Task | `- **Task:** …` (optional if empty) |

**Command:**

```bash
python3 scripts/sync_vault_devlog.py --vault "$PRODUCT_VAULT_ROOT"
# usually via: python3 scripts/sync_docs_full.py --vault "$PRODUCT_VAULT_ROOT"
```

**Do not** hand-write a `… synced` block. Title must contain `synced` and a semver.

### 2. Ad-hoc note (mid-task / handoff)

**Header shape:**

```markdown
## YYYY-MM-DD — {short title}
```

**Required fields:**

| Field | Example |
|-------|---------|
| When | `- **When:** … UTC · … HKT` |
| Kind | `- **Kind:** note` |
| Repo | `- **Repo**: <project_label>` |
| Bullets | `- Changed: …` / `- Outcome: …` (prefer `Key: value`) |

**Forbidden in note titles:**

- the word `synced` (any case)
- bare semver alone (`v1.2.3` as the whole title)

**Command:**

```bash
python3 scripts/sync_vault_devlog.py --note "Soft gate tests" \
  --bullet "Changed: scripts/cross_review_gate.py" \
  --bullet "Tests: pytest 6 passed" \
  --bullet "Outcome: soft warn on large diffs"
```

Night-shift readiness may append at most **one note per product per UTC day** (dedupe marker `Night shift readiness <label> YYYY-MM-DD`). Prefer detail in `night-shift-log.md` / `TODO.md`.

---

## Product plugin (required for correct path)

```yaml
vault:
  enabled: true                    # or false to skip vault
  root_env: PRODUCT_VAULT_ROOT
  default_root: ""                 # optional machine default; leave empty in public clones
  project_label: my-product
  dev_log_rel: 01-Projects/my-product/dev-log.md
```

New products: set `project_label` + `dev_log_rel` when enabling vault.  
Seed empty log:

```bash
python3 scripts/ensure_dev_log.py --vault "$PRODUCT_VAULT_ROOT"   # creates header if missing
```

---

## New product checklist

1. `install_into_product.sh` (or rsync) so `scripts/sync_vault_devlog.py` + `vault_resolve.py` are present.  
2. Fill `vault.project_label` / `dev_log_rel` in product_plugin.  
3. `export PRODUCT_VAULT_ROOT=…` on the machine that owns the vault.  
4. `python3 scripts/ensure_dev_log.py --vault "$PRODUCT_VAULT_ROOT"` once.  
5. After tasks: `--note`; after release: `/sync_docs` only for `synced` rows.  
6. Do **not** copy another product’s freeform log style.

---

## Related

| Doc | Role |
|-----|------|
| [second-brain-optional.md](second-brain-optional.md) | Vault enablement |
| [ship-flow.md](ship-flow.md) | When release vs note runs |
| [night-shift.md](night-shift.md) | Separate `night-shift-log.md` template |
| `scripts/sync_vault_devlog.py` | Writer implementation |
| `scripts/ensure_dev_log.py` | Seed / normalize header |
| `tests/test_sync_vault_devlog_format.py` | Contract tests |

**Anti-patterns:** freeform append; mixing release shape into notes; product-local rewrite of field names; absolute path prose without **Repo**/**When**/**Kind**.
