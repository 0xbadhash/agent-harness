---
name: audit_repo
description: Read-only codebase scan against ENGINEERING_ASSURANCE.md policy.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
preserve-artifacts-on-failure: true
---
# Reads: ENGINEERING_ASSURANCE.md, entire source tree
# Writes: PRODUCTION_GAP_ANALYSIS.md, WORKFLOW_DOCUMENTATION.md (DRIFT TRACKER, manual)
# Anti-patterns: docs/AGENT_REFERENCE.md
When invoked with `/audit_repo`:
1. Pre-condition: phase ∈ {init, shipped, blocked}
2. Scan codebase against policy (read-only; no edits)
3. Generate or update PRODUCTION_GAP_ANALYSIS.md with GAP/DOC/OPS entries
4. Include §9 "Things that look bad but are actually fine" (≥3 entries)
5. Update WORKFLOW_DOCUMENTATION.md DRIFT TRACKER by hand (no auto script)
6. Output: `✅ AUDIT COMPLETE. Run /plan_backend` if roadmap changes needed
