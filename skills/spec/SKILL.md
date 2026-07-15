---
name: spec
description: >
  Constitution-aware interview and clarify pass that produces a buildable spec
  (what/why), optional technical plan (how), tickets, and a product-roadmap OPEN
  item for /execute_dev. Use for /spec, "write a spec", "spec this idea", before
  coding. Optional --plan. If Spec Kit (.specify/) is present, prefer the bridge
  skill or map to /speckit.* then return here for roadmap/handoff. Not for
  implementation (/execute_dev) or compliance scoring (/pr_review).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 900
preserve-artifacts-on-failure: true
---
# Reads: product_plugin.yaml, constitution (see §0), product roadmap, pipeline.json, product layout
# Writes: .agents/specs/<slug>.md, optional …-plan.md, optional tickets/, roadmap OPEN item
# Anti-patterns: policy/AGENT_REFERENCE.md
# Depth: references/spec-template.md · plan-template.md · clarify-checklist.md · provenance.md
# Bridge: references/speckit-bridge.md (when .specify/ exists — do not install Spec Kit from this skill)

When invoked with `/spec` (args: idea text, `--from-conversation`, `--no-interview`,
`--no-clarify`, `--plan`, `--tickets`, `--linear`, `--github`, `--skip-constitution-warn`):

## 0. Pre-condition + constitution

1. Read `.agents/product_plugin.yaml` — `product_roadmap`, `stack`, `smoke`, `product_path_prefixes`, `domain_review_hints`.
2. Read `.agents/state/pipeline.json` — **do not change phase**.
   - If `phase` ∉ {`init`, `blocked`, `shipped`} → warn in-flight ship; still allow a *future* roadmap item.
3. Dirty working tree: note only (spec is docs-only).
4. **Constitution read (required attempt):** load the first file that exists:
   1. `.agents/CONSTITUTION.md`
   2. `AGENTS.md` (product root)
   3. `.agents/policy/base_constraints.md` + skim `ENGINEERING_ASSURANCE.md` headers
   - Hold principles for the whole run (quality, TDD, security, scope discipline).
   - If none found and not `--skip-constitution-warn` → print once:  
     `⚠️ No CONSTITUTION.md — using policy defaults. Consider adding .agents/CONSTITUTION.md (see templates/CONSTITUTION.example.md).`
5. **Spec Kit detect (optional bridge):** if `.specify/` exists → read `references/speckit-bridge.md` and either:
   - Hand off to Spec Kit commands for specify/clarify/plan/tasks, then resume at §6 (roadmap OPEN pointing at `specs/…`), **or**
   - Stay on this skill but prefer Spec Kit artifact paths if the user already produced them.

## 1. Mode selection

| Flag / situation | Mode |
|------------------|------|
| Default `/spec "idea"` | Interview → **draft** → **clarify** → finalize |
| `--from-conversation` | Synthesize draft → **clarify** (only remaining gaps) |
| `--no-interview` + enough text | Draft only; halt `🛑 SPEC MISSING` if acceptance vague |
| `--no-clarify` | Skip structured clarify (spikes only — say so in the spec) |
| `--plan` | Also write technical plan file after clarify |
| Complex / multi-slice | Offer **`--tickets`** after plan (or after spec if no plan) |

## 2. Explore before asking

Look up facts in the product tree (`stack.app_layout` / `product_path_prefixes`).  
**Ask only decisions and unknowns.** Use product domain vocabulary.

## 3. Interview (what / why — not stack)

Goals: enough clarity for a **draft** spec (problem, solution, stories, acceptance draft).

Rules:
- One question at a time; recommended default each time.
- Prefer short decision tree; stop when draft is possible.
- **Do not** lock tech stack here unless the user forces it (stack belongs in `--plan` or plugin defaults).

Minimum coverage (skip answered):

1. Outcome — done looks like…  
2. Scope — in / out  
3. Surfaces — product areas  
4. Constraints — from constitution + product (security, a11y, brand)  
5. Risks  
6. Verify — smoke + manual  
7. Priority  

If user says “you decide” → apply recommended defaults; record under Implementation Decisions or plan.

## 4. Draft the spec (what / why)

Write draft:

```text
.agents/specs/<YYYY-MM-DD>-<slug>.md
```

Use `references/spec-template.md`. Status line: `draft` until clarify completes.

Rules:
- Domain language over fragile paths.
- Acceptance criteria **checkable** (pass/fail).
- Align with constitution (call out any tension under Further Notes).

## 5. Clarify pass (required unless `--no-clarify`)

Structured gap-closing **after** draft, **before** ready-for-agent / plan / tickets.

1. Read `references/clarify-checklist.md`.
2. Scan draft for underspecification (actors, edge cases, non-goals, verify, data, permissions, failure modes).
3. Ask **one** clarifying question at a time (max ~8 unless user invites more).
4. Append answers under `## Clarifications` in the same spec file:

```markdown
## Clarifications

### 2026-07-15
- Q: …?
  - A: …
```

5. Update Problem / Solution / Acceptance / Out of Scope to match answers.
6. Set status to `ready-for-agent` when acceptance is checkable.

Halt `🛑 SPEC MISSING` if clarify cannot produce checkable acceptance.

## 6. Optional technical plan (`--plan` or agent recommendation)

When the change needs architecture/stack choices (new modules, APIs, multi-layer), or user passed `--plan`:

Write:

```text
.agents/specs/<YYYY-MM-DD>-<slug>-plan.md
```

Use `references/plan-template.md`. **How**, not what — stack from `product_plugin` + user constraints.  
Link plan from the main spec (`**Plan:** …`).  
Skip plan for pure copy/IA micro-changes unless asked.

## 7. Seams (TDD handoff)

Highest useful public contract → Testing Decisions (or plan).  
No unit suite → behavior + plugin smoke. `/execute_dev` owns red→green.

## 8. Roadmap item (required)

Append OPEN item to `product_plugin.product_roadmap`:

```markdown
### [OPEN] <short title>
- **Status:** open
- **Priority:** P0 | P1 | P2
- **Spec:** `.agents/specs/<file>.md`
- **Plan:** `.agents/specs/<file>-plan.md`   # if any
- **Acceptance:**
  - [ ] …
- **Smoke:** product smoke from plugin + manual path from spec
- **Notes:** one-line context
```

Ensure `## Open work` exists. Mark `**Next:** true` or place first for default `/execute_dev` target.

## 9. Optional tickets (`--tickets`)

After clarify (and plan if any):

1. Vertical tracer bullets + blockers.  
2. User approves granularity.  
3. `.agents/specs/<slug>/tickets/01-….md`  
4. Roadmap lists ticket dir; `/execute_dev` one unblocked ticket at a time.

## 10. Optional tracker publish

Default **local**. `--linear` / `--github` if credentials exist; else paste-ready body. No secrets in issues.

## 11. Handoff (do not implement)

```text
✅ SPEC READY
   spec:  .agents/specs/<…>.md
   plan:  .agents/specs/<…>-plan.md   # if any
   next:  /execute_dev
   then:  /cross_review (if large) → /pr_review → /release_mgmt → /sync_docs
```

- Do **not** edit product source, run TDD, or advance `pipeline.json`.  
- Constitution tensions resolved or documented.

## Failure modes

| Halt | When |
|------|------|
| `🛑 SPEC MISSING` | No checkable acceptance after clarify |
| `🛑 ROADMAP WRITE FAILED` | Cannot update roadmap path |
| `⏱️ TIMEOUT` | Preserve draft under `.agents/specs/` |

## Pipeline position

```text
/spec (+ constitution, clarify, optional plan/tickets)
  → /execute_dev → /cross_review → /pr_review → /release_mgmt → /sync_docs
```
