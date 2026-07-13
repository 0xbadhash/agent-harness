---
name: cross_review
description: Multi-persona review (Security, Maintainability, Domain) before or after pr_review.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Reads: git diff, ENGINEERING_ASSURANCE.md, docs/SECURITY.md, docs/AGENT_REFERENCE.md
# Writes: PR_DRAFT.md (section) or .agents/traces/<id>.md — does not advance pipeline phase
# Anti-patterns: docs/AGENT_REFERENCE.md

When invoked with `/cross_review`:
0. Read `GEMINI.md` routing + this skill.
1. Scope: uncommitted diff, or `--diff A..B`, or named paths from user.
2. Run **three personas** (each ≥3 concrete findings or explicit “none”):
   - **Security Guru** — auth, CSRF, secrets, injection, SSRF, cache poisoning (`docs/SECURITY.md`)
   - **Maintainability Expert** — coupling, dead code, testability, file boundaries (`GEMINI.md`)
   - **Domain Specialist** — watchlist/risk correctness, stale data honesty, desk UX contracts
3. Merge into a single report with severity: `blocker` | `major` | `nit`
4. Include §9 (≥3 entries) for intentional oddities.
5. Write evidence for soft gate (either):
   - Append `## Cross-review` section to `PR_DRAFT.md` with summary + severity counts, **or**
   - Write `.agents/artifacts/CROSS_REVIEW.md` with the same content (include marker `CROSS-REVIEW`).
6. Output: `✅ CROSS-REVIEW DONE` + blocker count. **Do not** set pipeline phase (use `/pr_review` for score gate).

If any **blocker** remains → recommend `/execute_dev` remediation before release.  
Then: `/pr_review --validate`.
