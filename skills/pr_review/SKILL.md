---
name: pr_review
description: >
  Deterministic compliance scoring (≥95% rubric). Soft cross_review gate on large diffs;
  prose-only skip guidance; secrets scan; pairs with product smoke (behavior ≠ source).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Reads: git diff, PR_DRAFT.md, product roadmap (optional), .agents/artifacts/CROSS_REVIEW.md
# Writes: PR_DRAFT.md, pipeline → approved/blocked
# Anti-patterns: policy/AGENT_REFERENCE.md

When invoked with `/pr_review --validate`:

1. Pre-condition: phase = `ready_for_review` (else `🛑 WRONG STATE`).

2. **Scope / prose-only:**

   ```bash
   python3 scripts/review_scope.py --base <base> --head HEAD --json
   ```

   - If `skip_heavy_review=true` (internal prose only): soft-warn if no CROSS-REVIEW; do not
     demand full multi-persona theater. Still require §9 and score.

3. **Secrets:**

   ```bash
   python3 scripts/check_secrets_diff.py --base <base> --head HEAD
   ```

   Findings → treat as block for ship (fail closed).

4. **PR_DRAFT narrative (soft):** Prefer filled sections from `templates/PR_DRAFT.md`:
   **What Problem This Solves**, **Why This Change Was Made**, **User Impact**, **Evidence**
   (warn if missing; not scored unless product hardens later).

5. **Cross-review (soft, recommended before score):**
   - Prefer `/cross_review` when the diff is **large** (≥8 files, ≥200 line churn, or ≥3 paths
     under `product_plugin.product_path_prefixes`) **and** not prose-only.
   - Prefer `/code_review` for non-trivial **code** when a second model is available.
   - Record `CROSS-REVIEW` / `CODE-REVIEW` markers under `PR_DRAFT.md` or `.agents/artifacts/`.
   - Soft gate: `python3 scripts/cross_review_gate.py --diff <range>`
   - Optional hard: `pr_validator.py --strict-cross-review`

6. **Behavior proof (behavior ≠ source):** Prefer product smoke / `validate full` already green
   in this session; warn if no smoke ran for runtime-touching diffs.

7. Run: `scripts/pr_validator.py --diff HEAD~1..HEAD` (or `vX.Y.Z..HEAD`)

8. Verify §9 has ≥3 entries

9. Score ≥95% → `approved`; else `blocked` + remediation

10. Output: `✅ APPROVED (score: X%)` or `❌ BLOCKED (score: X%)` plus soft-gate warnings

```
[/code_review] → /cross_review → /pr_review --validate → [product infra] → /release_mgmt → /sync_docs
```
