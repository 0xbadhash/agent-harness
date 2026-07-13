---
name: pr_review
description: Deterministic compliance scoring (≥95% rubric). Soft cross_review gate on large diffs.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Reads: git diff, BACKEND_ROADMAP.md, PR_DRAFT.md, .agents/artifacts/CROSS_REVIEW.md
# Writes: PR_DRAFT.md, pipeline → approved/blocked
# Anti-patterns: docs/AGENT_REFERENCE.md

When invoked with `/pr_review --validate`:
1. Pre-condition: phase = ready_for_review
2. **Cross-review (soft, recommended before score):**
   - Prefer `/cross_review` first when the diff is **large** (heuristic: ≥8 files, ≥200 line churn, or ≥3 `migration/` / design product paths).
   - Record outcome in `PR_DRAFT.md` under `## Cross-review` (or marker `CROSS-REVIEW`) **or** write `.agents/artifacts/CROSS_REVIEW.md`.
   - Soft gate: `python3 scripts/cross_review_gate.py --diff <range>` warns if large + no evidence; **does not block** score.
   - Optional hard gate: `pr_validator.py --strict-cross-review` (exit 1 on warn).
3. Run: `scripts/pr_validator.py --diff HEAD~1..HEAD --write-pr-draft` (or release range e.g. `vX.Y.Z..HEAD`)
4. Verify §9 section exists and has ≥3 entries (numbered or bullets)
5. Score ≥95% → phase = approved; else phase = blocked + remediation list
6. Output: `✅ APPROVED (score: X%)` or `❌ BLOCKED (score: X%)` plus any soft-gate warnings

Recommended ship sequence:
```
/cross_review  →  /pr_review --validate  →  /vps_infra_ops --verify  →  /release_mgmt  →  /sync_docs
```
