---
name: pr_review
description: Deterministic compliance scoring (≥95% rubric). Soft cross_review gate on large diffs.
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
1. Pre-condition: phase = ready_for_review
2. **PR_DRAFT narrative (soft, process honesty):** Prefer filled sections from `templates/PR_DRAFT.md`:
   **What Problem This Solves**, **Why This Change Was Made**, **User Impact**, **Evidence**
   (warn in output if missing; not scored by `pr_validator` unless product hardens later).
3. **Cross-review (soft, recommended before score):**
   - Prefer `/cross_review` when the diff is **large** (≥8 files, ≥200 line churn, or ≥3 paths under `product_plugin.product_path_prefixes`).
   - Record in `PR_DRAFT.md` under `## Cross-review` / marker `CROSS-REVIEW`, or `.agents/artifacts/CROSS_REVIEW.md`.
   - Soft gate: `python3 scripts/cross_review_gate.py --diff <range>` warns if large + no evidence.
   - Optional hard gate: `pr_validator.py --strict-cross-review`.
4. Run: `scripts/pr_validator.py --diff HEAD~1..HEAD` (or release range `vX.Y.Z..HEAD`)
5. Verify §9 has ≥3 entries
6. Score ≥95% → approved; else blocked + remediation
7. Output: `✅ APPROVED (score: X%)` or `❌ BLOCKED (score: X%)` plus soft-gate warnings

```
/cross_review → /pr_review --validate → [product infra] → /release_mgmt → /sync_docs
```
