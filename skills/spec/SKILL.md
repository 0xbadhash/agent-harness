---
name: spec
description: >
  Interview the user until the idea is buildable, then write a detailed spec with
  acceptance criteria and a product-roadmap OPEN item for /execute_dev. Optional
  Linear/GitHub publish and ticket split. Use for /spec, "write a spec",
  "spec this idea", before coding. Not for implementation (/execute_dev), not for
  compliance scoring (/pr_review), not product-only host/deploy skills.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Reads: product_plugin.yaml, product roadmap (plugin path), pipeline.json, product layout (explore)
# Writes: .agents/specs/<slug>.md, product roadmap OPEN item, optional .agents/specs/<slug>/tickets/
# Anti-patterns: policy/AGENT_REFERENCE.md
# Sources: Finn Loop /spec · Matt Pocock to-spec + grill + to-tickets · Fable-style autonomous brief
# Depth: references/spec-template.md · references/provenance.md

When invoked with `/spec` (optional args: idea text, `--from-conversation`, `--no-interview`, `--tickets`, `--linear`, `--github`):

## 0. Pre-condition

1. Read `.agents/product_plugin.yaml` — `product_roadmap`, `stack`, `smoke`, `product_path_prefixes`, `domain_review_hints`.
2. Read `.agents/state/pipeline.json` — **do not change phase**. `/spec` only prepares work.
   - If `phase` ∉ {`init`, `blocked`, `shipped`} → warn an in-flight ship exists; still allow a *future* roadmap item; do not start `/execute_dev` until the pipeline is free.
3. Dirty working tree: note it; do **not** block (spec is docs-only).

## 1. Mode selection

| Flag / situation | Mode |
|------------------|------|
| Default `/spec "idea"` | **Interview** (Finn + Matt grill), then synthesize |
| `--from-conversation` or rich prior chat | **Synthesize** (Matt `to-spec`); interview only for remaining gaps |
| `--no-interview` + enough text in args | Synthesize only; halt `🛑 SPEC MISSING` if acceptance still vague |
| Complex / multi-slice after draft | Offer **`--tickets`** (Matt `to-tickets`) |

## 2. Explore before asking

Look up what you can in the **product** tree (layout from plugin `stack.app_layout` / `product_path_prefixes`).  
**Ask only for decisions and unknowns** — not for facts the repo already holds.  
Use the product’s domain vocabulary from docs/glossary if present.

## 3. Interview (Finn “super plan mode” + Matt grilling)

Goals: enough clarity that `/execute_dev` will **not** hit `SPEC MISSING`.

Rules:
- Ask **one question at a time**; wait for the answer.
- For each question, give a **recommended default** using plugin stack + product context.
- Prefer a short decision tree over a long questionnaire.
- Stop when you can write: problem, solution, checkable acceptance criteria, out of scope, verify/smoke plan.

Minimum coverage (skip any already answered):

1. **Outcome** — what “done” looks like for the user/operator  
2. **Scope** — in / out  
3. **Surfaces** — modules/areas under `product_path_prefixes`  
4. **Constraints** — security, a11y, brand, platform limits from product  
5. **Risks** — secrets, deploy, third-party integrations  
6. **Verify** — how we know it works (plugin `smoke[]` + any manual path)  
7. **Priority** — P0/P1/P2 and blockers  

If the user says “you decide” → apply recommended defaults and state them under Implementation Decisions.

Large features: after a draft, ask whether to split into tracer-bullet tickets (`--tickets`).

## 4. Seams (Matt / TDD handoff)

Sketch **test seams** at the highest useful public contract. Prefer few seams; confirm when non-obvious.  
Record under **Testing Decisions**. `/execute_dev` drives red→green (or docs-only N/A).  
If the product has no unit suite yet, default seam = observable behavior + plugin smoke commands.

## 5. Write the spec artifact

```text
.agents/specs/<YYYY-MM-DD>-<slug>.md
```

Use `skills/spec/references/spec-template.md` (installed as `.agents/skills/spec/references/spec-template.md`).

Rules:
- Domain language over fragile file paths.  
- Avoid stale code snippets; exception: small decision-rich shapes from a prototype.  
- Acceptance criteria must be **checkable** (pass/fail).

## 6. Roadmap item (required — feeds `/execute_dev`)

Append or update an open item in `product_plugin.yaml` → `product_roadmap`.

```markdown
### [OPEN] <short title>
- **Status:** open
- **Priority:** P0 | P1 | P2
- **Spec:** `.agents/specs/<file>.md`
- **Acceptance:**
  - [ ] …
  - [ ] …
- **Smoke:** product smoke from plugin + any manual path in the spec
- **Notes:** one-line context
```

Ensure a `## Open work` section exists in the roadmap file if missing.  
One primary OPEN item should be the default for the next `/execute_dev` unless the user names another (`**Next:** true` or first under Open work).

## 7. Optional ticket split (`--tickets`)

1. Propose vertical tracer-bullet tickets (demoable; blocking edges).  
2. User approves granularity.  
3. Write `.agents/specs/<slug>/tickets/01-….md` …  
4. Roadmap item lists the ticket dir; `/execute_dev` takes **one** unblocked ticket at a time.

Wide mechanical refactors: expand/contract notes — do not force into fake vertical slices.

## 8. Optional tracker publish

**Default: local only.**

| Flag | Action |
|------|--------|
| `--linear` | If credentials available, create issue(s); else paste-ready markdown |
| `--github` | `gh issue create` when authenticated; else paste-ready body |

Never invent credentials. Never put secrets in issue bodies.

## 9. Handoff (do not implement)

```text
✅ SPEC READY
   next: /execute_dev
   then: /cross_review (if large) → /pr_review → /release_mgmt → /sync_docs
```

- **Do not** edit product source, run TDD, or advance `pipeline.json`.  
- Show paths to the spec file + roadmap section.

## Failure modes

| Halt | When |
|------|------|
| `🛑 SPEC MISSING` | Cannot write checkable acceptance |
| `🛑 ROADMAP WRITE FAILED` | Cannot update plugin roadmap path |
| `⏱️ TIMEOUT` | Preserve partial `.agents/specs/` draft |

## Pipeline position

```text
/spec → /execute_dev → /cross_review → /pr_review → /release_mgmt → /sync_docs
```
