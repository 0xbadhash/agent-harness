# Source of truth (agent OS vs products)

## Hierarchy

| Layer | Repository | Owns |
|-------|------------|------|
| **Agent OS** | **This repo (`agent-harness`)** | Shared **skills**, **policies**, ship workflow, install scripts |
| **Product** | catalyxt, watchlist, email-detach, substack-push, … | Domain code, product docs, `product_plugin.yaml`, product-only skills |
| **Knowledge vault** | Optional (e.g. second-brain) | Mirrors and logs only — **never** SoT for skills/policies |

## Rules

1. Edit skills and shared policies **here**, then re-run `install_into_product.sh` on products.
2. Product `.agents/skills` and `.agents/policy` are **install targets**, not independent masters of shared content.
3. Product-only skills: declare in `product_plugin.yaml` → `product_skills` and keep under product `.agents/skills/<name>/`.
4. A personal Obsidian/second-brain vault may **mirror** harness or product docs for browsing; mirrors are overwritten and must not be edited as truth.

## What this harness is not

- Not a product feature codebase  
- Not an Obsidian vault  
- Not coupled to any one host path (`/opt/second-brain` is **not** a default)
