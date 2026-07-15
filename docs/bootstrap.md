# Bootstrap

Install the harness into a product without binding a technology.

## Prerequisites

- `git`, `bash`, `rsync`, `python3`  
- A coding agent that can load `SKILL.md` from `.agents/skills/` (or your agent’s skill path)  
- Network only if you use remote vaults / package registries (optional)

## Path A — New product

```bash
# 1. Harness (pin a tag for stability)
git clone --branch v1.0.0 --depth 1 \
  https://github.com/0xbadhash/agent-harness.git ~/agent-harness
export AGENTS_HARNESS_ROOT=~/agent-harness

# 2. Empty product
mkdir my-product && cd my-product
git init

# 3. Install
"$AGENTS_HARNESS_ROOT/install_into_product.sh" .

# 4. Choose stack at bootstrap (edit plugin)
cp -n "$AGENTS_HARNESS_ROOT/product_plugin.example.yaml" \
      .agents/product_plugin.yaml   # if not created
$EDITOR .agents/product_plugin.yaml
```

### What to set in the plugin first

| Field | Meaning |
|-------|---------|
| `product_id` / `product_name` | Identity |
| `stack` | Free-form labels: language, runtime, test runners (documentation for the agent) |
| `smoke` | Commands that prove the product works after a change |
| `product_path_prefixes` | Paths treated as “product code” for large-diff heuristics |
| `vault` | Optional second-brain / notes root (or disable) |

**You choose the stack.** Examples (not requirements):

```yaml
stack:
  languages: [typescript]      # or [python], [go], [rust], [php], …
  package_manager: pnpm        # or npm, cargo, poetry, …
  test_runners: [vitest, tsc]  # whatever you actually run
  app_layout: src/             # your convention
```

Smoke is how the harness verifies *your* world:

```yaml
smoke:
  - name: unit
    cmd: ["pnpm", "test"]      # or pytest, go test, cargo test, …
  - name: typecheck
    cmd: ["pnpm", "exec", "tsc", "--noEmit"]
```

## Path B — Existing product

```bash
cd /path/to/existing-product
export AGENTS_HARNESS_ROOT=~/agent-harness
"$AGENTS_HARNESS_ROOT/install_into_product.sh" .
# fill .agents/product_plugin.yaml
# keep product-only skills (deploy, hosts) under .agents/skills/<name>/
```

## What install writes

| Path | Purpose |
|------|---------|
| `.agents/skills/*` | Portable skills (overwrites same names) |
| `scripts/*` | Gate scripts (vendored copy) |
| `.agents/policy/*` | Policy snapshot |
| `.agents/state/pipeline.json` | FSM (created if missing) |
| `.agents/product_plugin.yaml` | **Your** bootstrap choices |
| `.agents/HARNESS_ROOT` | Pointer to global clone |

Product-only skill directories (names not in the harness) are **not deleted**.

## First agent session

1. Point the agent at the product repo.  
2. Confirm skills are visible under `.agents/skills/`.  
3. Prefer `/spec "tiny idea"` first (constitution + clarify; optional `--plan` / `--tickets`) so acceptance criteria land on the product roadmap.  
4. Optionally copy `templates/CONSTITUTION.example.md` → product `.agents/CONSTITUTION.md`.  
5. Run `/execute_dev` (loads OPEN roadmap item or args). Expect **TDD**: failing tests first for code changes.

## Verify install

```bash
test -f .agents/product_plugin.yaml && echo plugin_ok
test -f .agents/skills/execute_dev/SKILL.md && echo skills_ok
test -f .agents/skills/spec/SKILL.md && echo spec_ok
python3 scripts/pipeline_state.py get 2>/dev/null || cat .agents/state/pipeline.json
python3 scripts/verify_skills.py
```

## Next

- [Product plugin reference](product-plugin.md)  
- [Ship flow](ship-flow.md)  
- [TDD](tdd.md)  
