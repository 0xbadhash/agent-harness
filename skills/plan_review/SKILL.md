---
name: plan_review
description: >
  Pre-code adversarial review of a technical plan (-plan.md) before /execute_dev.
  Use for large non-waiver ships after /spec --plan. Writes PLAN_REVIEW.md.
  Not a ship FSM phase. Fail-closed via check_outer_loop / hard_gates when plan required.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
---
# Reads: Spec + Plan paths from PR_DRAFT or args; constitution; product_plugin
# Writes: .agents/artifacts/PLAN_REVIEW.md
# Anti-patterns: policy/AGENT_REFERENCE.md

When invoked with `/plan_review` (args: optional plan path):

## 0. Pre-condition

1. Resolve plan: CLI path, or `**Plan:**` in PR_DRAFT, or Spec frontmatter.
2. If no plan → halt `🛑 NO PLAN` (run `/spec --plan` first for large work).
3. Do **not** advance `pipeline.json`.

## 1. Personas (short)

Apply at least two lenses:

| Persona | Ask |
|---------|-----|
| Product | Wrong surface / wrong user / overbuild? |
| Security | Secrets, authz, fail-closed, data loss? |
| Ops | Smoke path, rollback, night bar impact? |

## 2. Write artifact

```text
.agents/artifacts/PLAN_REVIEW.md
```

Must include:

- **Marker:** `PLAN-REVIEW`
- **Plan:** path
- **Verdict:** PASS | FAIL | REVISE
- ≥2 findings **or** explicit “no material issues” with justification
- Body ≥160 characters

## 3. Handoff

```text
✅ PLAN REVIEW DONE
   verdict: PASS|FAIL|REVISE
   next: /execute_dev   # only if PASS
   if REVISE/FAIL: edit plan → re-run /plan_review
```

## Related

- Outer loop playbook: `docs/outer-loop-playbook.md`
- Gate: `python3 scripts/check_outer_loop.py`
