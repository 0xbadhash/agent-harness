---
name: spec
description: >
  Constitution-aware grill-me interview (mandatory by default) that produces a
  buildable spec (what/why), optional technical plan (how), tickets, and a
  product-roadmap OPEN item for /execute_dev. Prefer asking the operator over
  inventing product decisions. Use for /spec, "write a spec", "spec this idea",
  before coding. Optional --plan / --tickets. Spike-only skip via --spike (must
  document). If Spec Kit (.specify/) is present, prefer the bridge then return
  for roadmap/handoff. Not for implementation (/execute_dev) or scoring (/pr_review).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 900
preserve-artifacts-on-failure: true
---
# Reads: product_plugin.yaml, constitution (see §0), product roadmap, pipeline.json, product layout
# Writes: .agents/specs/<slug>.md, optional …-plan.md, optional tickets/, roadmap OPEN item
# Anti-patterns: policy/AGENT_REFERENCE.md
# Depth: references/spec-template.md · plan-template.md · grill-me-checklist.md ·
#        clarify-checklist.md · provenance.md
# Bridge: references/speckit-bridge.md (when .specify/ exists — do not install Spec Kit from this skill)

When invoked with `/spec` (args: idea text, `--from-conversation`, `--plan`,
`--tickets`, `--spike`, `--linear`, `--github`, `--skip-constitution-warn`):

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
   - Hand off to Spec Kit commands for specify/clarify/plan/tasks, then resume at §7 (roadmap OPEN pointing at `specs/…`), **or**
   - Stay on this skill but prefer Spec Kit artifact paths if the user already produced them.
6. **Print once at start:**  
   `🔥 GRILL-ME ON — /spec asks before inventing product decisions. Answer one question at a time (or accept the recommended default).`

## 1. Mode selection

| Flag / situation | Mode |
|------------------|------|
| Default `/spec "idea"` | Explore → **grill-me** → draft → **clarify** → finalize |
| `--from-conversation` | Synthesize draft from thread → **grill remaining themes** → clarify gaps |
| `--spike` | **Only** allowed skip of full grill; must set `## Grill-me` **Status:** `spike-skipped` + reason ≥20 chars; still need checkable AC or halt |
| `--plan` | Also write technical plan file **after** grill + clarify |
| `--tickets` | Write ticket files **after** grill + clarify (and plan if any) |

**Removed (do not honor as free skips):**

- `--no-interview` — **ignored**; grill-me is the interview
- `--no-clarify` — **ignored**; clarify remains required for feature specs

If an agent or user passes those flags, print:  
`⚠️ --no-interview/--no-clarify are retired; grill-me + clarify are mandatory (use --spike only for true spikes).`

## 2. Explore before asking

Look up facts in the product tree (`stack.app_layout` / `product_path_prefixes`).  
**Ask only decisions and unknowns.** Use product domain vocabulary.  
Do **not** invent user preferences.

## 3. Grill-me interview (**mandatory** unless `--spike`)

**SoT checklist:** `references/grill-me-checklist.md` (themes G1–G7).

Goals: enough adversarial clarity that we do **not** ship the wrong product/feature.

Rules:

1. **One question at a time**; always offer a **recommended default**.
2. Cover required themes G1–G7 (or mark N/A with reason when truly inapplicable).
3. Prefer short decision tree; do not stop early because the agent “knows.”
4. **Do not** lock tech stack here unless the user forces it (stack → `--plan`).
5. Record **every** Q/A under `## Grill-me` in the spec file (create draft file early if needed).
6. If grill **rejects** the idea → status `rejected`; halt `🛑 GRILL REJECTED`; no plan/tickets.

Minimum coverage still includes outcome, scope, surfaces, constraints, risks, verify, priority — fold into G1–G7 rather than a separate optional interview.

If user says “you decide” → apply recommended default **and log it** under Grill-me.

### Spike path (`--spike`)

```markdown
## Grill-me

**Status:** spike-skipped
**Date:** <ISO date>
**Reason:** <≥20 characters why full grill was deferred>
```

Spikes still need checkable acceptance or `🛑 SPEC MISSING`.

## 4. Draft the spec (what / why)

Write draft:

```text
.agents/specs/<YYYY-MM-DD>-<slug>.md
```

Use `references/spec-template.md`. Status: `draft` until grill + clarify complete.

Rules:

- Domain language over fragile paths.
- Acceptance criteria **checkable** (pass/fail).
- Align with constitution (call out any tension under Further Notes).
- **`## Grill-me` section required** before `ready-for-agent`.

## 5. Clarify pass (**required** after draft)

Structured gap-closing **after** draft, **before** ready-for-agent / plan / tickets.

1. Read `references/clarify-checklist.md`.
2. Scan draft for remaining underspecification (not already answered in Grill-me).
3. Ask **one** clarifying question at a time (max ~8 unless user invites more).
4. Append under `## Clarifications` (separate from Grill-me).
5. Update Problem / Solution / Acceptance / Out of Scope to match.
6. Set status to `ready-for-agent` only when:
   - acceptance is checkable, **and**
   - grill evidence is complete (or spike-skipped with reason).

Halt `🛑 SPEC MISSING` if acceptance is not checkable.  
Halt `🛑 GRILL MISSING` if grill evidence fails `references/grill-me-checklist.md` rules.

## 6. Technical plan (`--plan` or agent recommendation)

When the change needs architecture/stack choices, or user passed `--plan`:

Write:

```text
.agents/specs/<YYYY-MM-DD>-<slug>-plan.md
```

Use `references/plan-template.md`. **How**, not what.  
Link from the main spec (`**Plan:** …`).  
**Never** write plan before grill completes (or spike documented).

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
- **Notes:** grill-me complete | spike-skipped
```

Ensure `## Open work` exists. Mark `**Next:** true` or place first for default `/execute_dev` target.

## 9. Tickets (`--tickets`)

After grill + clarify (and plan if any):

1. Vertical tracer bullets + blockers.  
2. User approves granularity when ambiguous.  
3. `.agents/specs/<slug>/tickets/01-….md`  
4. Roadmap lists ticket dir; `/execute_dev` one unblocked ticket at a time.

## 10. Optional tracker publish

Default **local**. `--linear` / `--github` if credentials exist; else paste-ready body. No secrets in issues.

## 11. Handoff (do not implement)

```text
✅ SPEC READY
   grill: complete | spike-skipped
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
| `🛑 GRILL MISSING` | Would mark ready without grill evidence (see checklist) |
| `🛑 GRILL REJECTED` | Operator cancelled idea during grill |
| `🛑 SPEC MISSING` | No checkable acceptance after clarify |
| `🛑 ROADMAP WRITE FAILED` | Cannot update roadmap path |
| `⏱️ TIMEOUT` | Preserve draft under `.agents/specs/` (keep Grill-me so far) |

## Pipeline position

```text
/spec (constitution → grill-me → draft → clarify → optional plan/tickets)
  → /execute_dev → /cross_review → /pr_review → /release_mgmt → /sync_docs
```

## Deterministic check

Ship path: `python3 scripts/check_spec_grill.py` (also invoked from `spec_gate.py` when Spec is linked and not waived).
