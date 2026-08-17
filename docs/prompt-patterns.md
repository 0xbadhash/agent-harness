# Prompt patterns → harness skills (P3)

**Audience:** operators and LLMs.  
**Source idea:** Jules White et al. *prompt pattern* catalog (reusable structures for LLM interaction) — mapped onto **existing** agent-harness skills.  
**Not a new FSM.** Patterns guide *how* to talk; skills + hard gates decide *what is allowed to ship*.

Related: [ship-flow-detailed.md](ship-flow-detailed.md) (CODER modes) · [skills-catalog.md](skills-catalog.md)

---

## CODER reminder (modes)

| Mode | Use for |
|------|---------|
| **C** Compute | Scripts, gates, exit codes — do not “reason past” them |
| **O** Organize | Specs, tickets, REMAINING, SESSION_CONTEXT |
| **D** Display | NEXT_SKILL line, STATUS, Mermaid, PUSH_PROOF |
| **E** Engineer | execute_dev, TDD, release |
| **R** Reason | Spec clarify, cross_review personas — **not** hard_gates |

Rule: **C → O → D → E**; open **R** only at decision points.

---

## Pattern → skill map

Patterns named in the spirit of White’s catalog (Persona, Template, Recipe, Error identification, etc.). Use the **skill**, not free-form chat, when the row says so.

| Pattern (intent) | What you want | Harness skill / script | Mode |
|------------------|---------------|------------------------|------|
| **Persona** | Multi-view critique | `/cross_review` | R (soft) |
| **Template** | Fixed output shape | `PR_DRAFT.md` template · `templates/PR_DRAFT.md` | O/D |
| **Recipe / chain** | Ordered steps | Ship FSM + `next_skill.py` | E/C |
| **Question refinement** | Clarify acceptance | `/spec` clarify pass | R |
| **Context manager** | Load state before work | `session_context.py --write` · `remaining_board.py` | O/D |
| **Error identification** | Fail closed on bad evidence | `hard_gates.py` · `/pr_review --validate` | C |
| **Alternative approaches** | “Why this design” | PR_DRAFT *Why This Change Was Made* | R |
| **Cognitive verifier** | Second pass on code | `/code_review` (P0-first) | E/R |
| **Fact check list** | AC ↔ tests | `## Traceability` hard gate | C/O |
| **Output automator** | Deterministic closeout | `run_ship_chain.py` (no LLM depth) | C |
| **Flipped interaction** | Human owns intent | `/spec` only human acceptance for features | R |
| **Game / constraint** | Scope freeze | `review_scope.py` + code_review scope governor | C/E |
| **Reflection** | After ship learning | `/retrospect` | O/R |
| **Infinite generation guard** | Stop loops | max 3 remediation cycles; night autofix ×1 | C |

---

## Anti-patterns (do not “pattern” around gates)

| Anti-pattern | Why forbidden |
|--------------|----------------|
| Prompt the model to “approve” without `pr_validator` | Hard score is Compute, not Reason |
| Skip TDD “because model is sure” | Red-proof hard gate |
| Invent next skill without `next_skill.py` | Routing contract |
| Night shift invents roadmap features | PROPOSE only with evidence |
| Free-form multi-agent debate as a ship phase | No sixth phase |

---

## Suggested prompts (thin wrappers)

### Session start (Organize + Display)

```text
Run: python3 scripts/session_context.py --write
Then: python3 scripts/remaining_board.py
Summarize SESSION_CONTEXT.md in ≤10 bullets. Do not invent next ship steps — follow NEXT_SKILL after any skill.
```

### Feature start (Reason → Organize)

```text
/spec for: <outcome>
Use constitution + clarify until acceptance is checkable. No implement yet.
```

### After implement (Engineer routing)

```text
/execute_dev completed for <task>.
Run: python3 scripts/next_skill.py --after execute_dev --base <base> --head HEAD
Execute exactly the printed NEXT_SKILL.
```

### Blocked score (Error identification)

```text
phase=blocked. Read PR_DRAFT violations and hard_gates output.
/execute_dev: fix only cited issues; re-run tests; do not expand scope.
```

---

## Maintenance

When adding a portable skill: add one row to the table above + Mode column in [skills-catalog.md](skills-catalog.md).  
Patterns never bypass [hard_gates.py](../scripts/hard_gates.py).
