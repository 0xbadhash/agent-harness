---
name: audit_repo
description: Read-only codebase scan against ENGINEERING_ASSURANCE.md policy plus whole-repo obsolete/cleanup scan (evidence only).
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
preserve-artifacts-on-failure: true
---
# Reads: ENGINEERING_ASSURANCE.md, entire source tree, .agents/policy/OBSOLETE_CLEANUP_SCAN.md
# Writes: PRODUCTION_GAP_ANALYSIS.md, WORKFLOW_DOCUMENTATION.md (DRIFT TRACKER, manual)
# Anti-patterns: docs/AGENT_REFERENCE.md / .agents/policy/AGENT_REFERENCE.md

When invoked with `/audit_repo`:
1. Pre-condition: phase ∈ {init, shipped, blocked}
2. Scan codebase against policy (read-only; no edits)
3. **Obsolete / cleanup scan (mandatory, whole-repo):** follow `.agents/policy/OBSOLETE_CLEANUP_SCAN.md`
   - Mode: **evidence only — no deletes**
   - Fold candidates into `PRODUCTION_GAP_ANALYSIS.md` as GAP/DOC/OPS entries with **confidence** and evidence
   - False friends (scaffolds, dual product stacks, intentional stubs) go in §9, not as delete recommendations
4. Generate or update PRODUCTION_GAP_ANALYSIS.md with GAP/DOC/OPS entries (include obsolete scan section or tags)
5. Include §9 "Things that look bad but are actually fine" (≥3 entries)
6. Update WORKFLOW_DOCUMENTATION.md DRIFT TRACKER by hand (no auto script)
7. Output: `✅ AUDIT COMPLETE` + obsolete Tier A count. Run `/plan_backend` if roadmap changes needed;
   for scripted hygiene-only without gap docs prefer `/sweep`.
