# Spec Kit bridge (optional — no install from this skill)

Use this when the product already has **[github/spec-kit](https://github.com/github/spec-kit)** (directory `.specify/` present).  
This harness skill does **not** run `specify init` or install Spec Kit.

## Detect

```text
.specify/          → Spec Kit project
specs/00N-*/       → feature specs (typical layout)
```

## Recommended ownership split

| Phase | Owner |
|-------|--------|
| constitution / specify / clarify / plan / tasks | Spec Kit (`/speckit.*`) when available |
| roadmap OPEN + pipeline ship | **This harness** |
| implement one ticket + TDD | `/execute_dev` |
| review / release / sync | `/cross_review` → `/pr_review` → `/release_mgmt` → `/sync_docs` |

## Bridge procedure for `/spec`

1. If user wants full SDD and Spec Kit is installed in-agent:  
   - Point them to `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks`  
   - Then **return** to harness §8 (roadmap): OPEN item **Spec:** path to `specs/00N-…/spec.md` and **Plan:** `…/plan.md` if present  
2. If Spec Kit artifacts already exist for this feature:  
   - Do **not** duplicate a full `.agents/specs/` rewrite unless asked  
   - Write roadmap OPEN pointing at existing Spec Kit paths  
   - Optionally copy a short pointer file: `.agents/specs/<slug>.md` with link + acceptance summary for agents that only scan `.agents/specs/`  
3. If Spec Kit is **not** present:  
   - Stay on harness `/spec` (constitution + clarify + optional plan)  
   - Never `curl | bash` or auto-install Spec Kit  

## Anti-patterns

- Running `/speckit.implement` **and** `/execute_dev` without one owner  
- Dual FSM (ignore Spec Kit “feature branch only”; ship phase is always `.agents/state/pipeline.json`)  
- Dropping harness review/release gates after Spec Kit plan  
