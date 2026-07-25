---
name: cross_review
description: >
  Multi-persona review (Security, Maintainability, Domain) before or after pr_review;
  Maintainability runs scoped obsolete/cleanup scan. P0-first; scope governor;
  optional prose-only skip. Complements /code_review.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Reads: git diff, ENGINEERING_ASSURANCE.md, docs/SECURITY.md, docs/AGENT_REFERENCE.md,
#        .agents/policy/OBSOLETE_CLEANUP_SCAN.md
# Writes: PR_DRAFT.md (section) or .agents/artifacts/CROSS_REVIEW.md — does not advance pipeline phase
# Anti-patterns: policy/AGENT_REFERENCE.md / .agents/policy/AGENT_REFERENCE.md

When invoked with `/cross_review`:

0. Read `GEMINI.md` routing + this skill.

1. **Scope baseline** (freeze before reviewing):

   ```bash
   python3 scripts/review_scope.py --base <base> --head HEAD --json
   ```

   - If `skip_heavy_review` / prose-only internal notes → short direct read; still write a minimal
     CROSS-REVIEW marker (“prose-only skip”) unless user asked for full personas.
   - **Scope governor:** only fix **in-scope blockers** from *this* diff. Pre-existing or adjacent
     issues → **follow-up**. New contracts / migrations / release-process → **stop-and-escalate**.
   - After **two** unproductive fix cycles → reclassify; do not expand past ~2× files or non-test LOC
     without explicit approval.

2. **Secrets (diff-scoped):**

   ```bash
   python3 scripts/check_secrets_diff.py --base <base> --head HEAD
   ```

   Fail closed on findings before persona write-up.

3. **Optional second-model code pass** for non-prose code diffs:

   - Prefer `/code_review` (different model when configured) before or after personas.
   - Clean code_review is **not** product proof — still run smoke/validate later.

4. Scope: uncommitted diff, or `--diff A..B`, or named paths from user.

5. Run **three personas** — default report **P0 / blockers only** (material break of flow,
   outcome, or safety). Include **major** only for concrete security. Nits only if user
   asks for a wide review. Each persona: ≥1 concrete finding **or** explicit “none”
   (do not invent filler nits).

   - **Security Guru** — auth, CSRF, secrets, injection, SSRF, cache poisoning (`docs/SECURITY.md`)
   - **Maintainability Expert** — coupling, dead code, testability, file boundaries (`GEMINI.md`)
     - **Required:** scoped **Obsolete / cleanup scan** from `.agents/policy/OBSOLETE_CLEANUP_SCAN.md`
       (touched paths + direct callers/callees only). Tier A/B/C + confidence ∈ [0,1] + evidence.
     - Whole-repo cruft: one line → “run `/sweep`” — do not full-repo scan unless asked.
   - **Domain Specialist** — product domain correctness (`product_plugin.domain_review_hints`)

6. Merge into a single report with severity: `blocker` | `major` | `nit`  
   Lead with **blocker count**; list follow-ups separately from ship-blockers.

7. Include §9 (≥3 entries) for intentional oddities.

8. Write evidence:
   - Append `## Cross-review` to `PR_DRAFT.md` with summary + severity counts +
     `### Obsolete / cleanup (scoped)`, **or**
   - Write `.agents/artifacts/CROSS_REVIEW.md` with marker `CROSS-REVIEW`.

9. **Re-review:** if you changed code for an accepted blocker, re-run focused tests and
   re-check the finding once. Stop when no accepted blockers remain.

10. Output: `✅ CROSS-REVIEW DONE` + blocker count + scoped obsolete Tier A count.  
    **Do not** set pipeline phase (use `/pr_review` for score gate).

If any **blocker** remains → recommend `/execute_dev` remediation before release.  
Then: product smoke / `validate full` → `/pr_review --validate`.

**Behavior ≠ source:** a clean cross-review is not proof the app works for users.
