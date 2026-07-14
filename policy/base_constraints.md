# Base Constraints (inherited by all skills)

## Product vs harness
- **Product** = application code + roadmap + domain (see `.agents/product_plugin.yaml`).
- **Harness** = skills, scripts, policy, pipeline FSM (this package / product `.agents/` install).
- Do not mix harness backlog into the product roadmap. Stack is chosen only in the product plugin.

## Router & workflow
- First action: product session policy (if any) + harness policy + skill for the task.
- After significant product change: run **smoke** from `product_plugin.yaml` (and targeted tests).
- Long tasks: optional worksheets under `.agents/traces/`.

## Pipeline
- State: `.agents/state/pipeline.json` via `scripts/pipeline_state.py` only (atomic).
- Flow: init → ready_for_review → approved → shipped → init (see docs/ship-flow.md).

## Handoff Discipline
- Read only files declared in the skill's Reads line
- Write only files declared in the skill's Writes line
- Include §9 "Things that look bad but are actually fine" in reports

## §9 Schema
Every completion report MUST include this section with **minimum 3 entries**:
```yaml
things_that_look_bad_but_are_fine:
  - file: "path:line"
    concern: "what looks wrong"
    why_fine: "intentional reason"
    validation: "command to verify"
```

## TDD Boundary (enforced by `/execute_dev` step 3)
- Red → Green → Refactor for every behavior/code change
- New tests must fail before implementation lands
- Docs-only: explicit TDD N/A in handoff
- PR_DRAFT narrative (see `templates/PR_DRAFT.md`): **What Problem This Solves**, **Why This Change Was Made**, **User Impact**, **Evidence**
- Optional **Red-proof** in PR_DRAFT: command that failed before green

## Anti-Patterns
- Never skip validation gates
- Never hard-code a product language/framework in portable skills

## Tooling
- Prefer argv smoke from product_plugin over ad-hoc shell
- Validate with `scripts/validate.py` when vendored
