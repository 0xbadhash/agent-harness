---
name: sweep
description: Repo hygiene sweep — drift, skills audit, stale branches, whole-repo obsolete/cleanup scan (evidence only).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Reads: git status, scripts/*, .agents/skills/*, .agents/policy/OBSOLETE_CLEANUP_SCAN.md
# Writes: optional worksheet under .agents/traces/; does not ship product releases
# Anti-patterns: docs/AGENT_REFERENCE.md / .agents/policy/AGENT_REFERENCE.md

When invoked with `/sweep`:
1. `git status -sb` — report dirty tree (do not auto-commit).
2. `python3 scripts/drift_detector.py`
3. `python3 scripts/verify_skills.py`
4. `python3 scripts/check_repo_hygiene.py` (or via `validate.py hygiene` if preferred)
5. If `gh` available: list remote branches; flag non-`main` as stale candidates (do not delete without user OK).
6. **Obsolete / cleanup scan (mandatory, whole-repo):** follow `.agents/policy/OBSOLETE_CLEANUP_SCAN.md`
   - Mode: **evidence only — no deletes**
   - Emit Tier A / B / C tables with confidence ∈ [0, 1] and evidence facts
   - Propose ordered cleanup; do not apply without user OK
7. Summarize actionable follow-ups; optional `generate_worksheet.py --task-id sweep-<date>` (include obsolete Tier A in worksheet if any).
8. Include §9 (≥3) for known noisy paths (e.g. `__pycache__`, vendor, intentional stubs).
9. Output: `✅ SWEEP DONE` + pass/fail counts + obsolete Tier A count.

Does **not** advance pipeline phase. For compliance score use `/pr_review`.  
Diff-scoped dead code only → `/cross_review`. Policy/gap framing → `/audit_repo`.
