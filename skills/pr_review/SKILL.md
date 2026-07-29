---
name: pr_review
description: >
  Deterministic compliance scoring (≥95% rubric) with hard gates pack: CODE-REVIEW,
  red-proof, secrets, behavior (runtime), spec/waiver. Soft cross_review on large diffs.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Reads: git diff, PR_DRAFT.md, .agents/artifacts/CODE_REVIEW.md, BEHAVIOR_REPORT.md
# Writes: pipeline → approved/blocked
# Anti-patterns: policy/AGENT_REFERENCE.md

When invoked with `/pr_review --validate`:

1. Pre-condition: phase = `ready_for_review` (else `🛑 WRONG STATE`).

2. **Scope / prose-only:**

   ```bash
   python3 scripts/review_scope.py --base <base> --head HEAD --json
   ```

3. **Hard gates pack** (fail closed — 25 pts all-or-nothing; see `scripts/hard_gates.py` + ship-flow):

   | Gate | Evidence |
   |------|----------|
   | Spec | `**Spec:** path` or `**Spec waiver:** hotfix\|chore\|docs-only\|prose-only` |
   | CODE-REVIEW | non-prose → `.agents/artifacts/CODE_REVIEW.md` marker |
   | Red-proof | non-prose → red_cmd/green_cmd or TDD N/A in PR_DRAFT |
   | BEHAVIOR | runtime non-prose → `.agents/artifacts/BEHAVIOR_REPORT.md` |
   | Secrets | `check_secrets_diff` clean on git range |

   ```bash
   python3 scripts/hard_gates.py --diff <base>...HEAD
   ```

   Emergency only: `pr_validator.py --skip-hard-gates`.

4. **PR_DRAFT narrative:** What Problem / Why / User Impact / Evidence + §9 (≥3).

5. **Cross-review (soft unless `--strict-cross-review`):** large diffs prefer CROSS-REVIEW artifact.

6. Run:

   ```bash
   python3 scripts/pr_validator.py --diff <base>...HEAD --update-pipeline
   ```

7. Score ≥95% → `approved`; else `blocked` + remediation list (read hard_gates violations first).

8. Output: `✅ APPROVED (score: X%)` or `❌ BLOCKED (score: X%)`

```
/code_review → [/cross_review|/behavior_validator] → /pr_review --validate
  → [infra?] → /release_mgmt → /sync_docs → [/qa_campaign]
```
