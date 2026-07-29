---
name: execute_dev
description: Implement one product or harness task with mandatory TDD. Product UI allowed when scoped; harness tasks use .agents/BACKLOG.md.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Pipeline: docs/ship-flow.md (in harness) / product docs
# Reads: product_plugin.yaml, product roadmap, .agents/BACKLOG.md, pipeline.json
# Writes: task tracker + pipeline → ready_for_review
# Anti-patterns: policy/AGENT_REFERENCE.md

When invoked with `/execute_dev`:
0. **Pre-condition Check:**
   - Read `.agents/state/pipeline.json`
   - If `phase` ∉ {`init`, `blocked`} → `🛑 WRONG STATE. Current: {phase}. Run /pr_review or /sync_docs first.` and halt.
   - If working tree dirty (`git status --porcelain` non-empty, ignore `__pycache__` if policy allows) → `🛑 DIRTY TREE. Commit or stash changes first.` and halt.
0b. **Spec gate (B1 — code ships):**
   ```bash
   python3 scripts/spec_gate.py --root .
   ```
   - Requires `**Spec:**` path (file exists) **or** `**Spec waiver:** hotfix|chore|docs-only|prose-only` in `PR_DRAFT.md`,
     or pipeline fields `spec_id` / `waiver` (`pipeline_state.py set-phase … --spec-id … --waiver …`).
   - Exit ≠ 0 → `🛑 SPEC MISSING` / waiver required and halt (docs-only tasks: use waiver `docs-only` or `prose-only`).
0c. **Context pack (B3 — recommended):**
   ```bash
   python3 scripts/context_pack.py --root .
   ```
1. **Load task:**
   - If user args specify a task → use that (acceptance must be clear).
   - Else product: first open priority item in the product roadmap file (see `product_plugin.yaml` → `product_roadmap`).
   - Else harness: first open row in `.agents/BACKLOG.md` / CHANGELOG Open work.
   - If none → `✅ ROADMAP EMPTY.`
2. **Spec check:** Missing acceptance criteria → `🛑 SPEC MISSING.` and halt.
   - For code ships, fill **## Traceability** (AC → test/smoke) in PR_DRAFT before `/pr_review` (hard gate B2).
3. **TDD (mandatory for behavior/code changes) — Red → Green → Refactor:**
   1. **Red:** Add or extend failing tests that express the public contract *before* (or with) the first implementation edit.
      - Optional helper: `scripts/scaffold_tests.py --task "<name>" --module "<target>"` (adapt to product layout).
      - Use the product's test runners from `product_plugin.yaml` → `stack` / project conventions.
      - Pure docs/policy-only: skip Red/Green but say so in handoff (no silent skip of code paths).
   2. **Prove Red:** Run the new/changed tests — they **must fail**. If they pass → `❌ OVER-SPECIFICATION` / wrong test; fix tests first.
   3. **Green:** Implement the minimum to make those tests pass. One sub-task only.
   4. **Refactor:** Clean up with tests still green.
   5. **Regression:** Run targeted suite + product smoke (from `product_plugin.yaml`) when runtime surface changes.
4. **Implement constraints + scope governor:**
   - **UI is allowed** when the product task is user-facing UI (use the product's own stack from `product_plugin.yaml`). Prefer progressive enhancement over unnecessary SPA rewrites unless the product already is an SPA.
   - Non-UI product work: APIs, services, CLIs, data paths as the product defines.
   - Harness-only changes stay under `.agents/` + `scripts/`.
   - Do not put harness backlog items into the product roadmap.
   - **Freeze scope** to the loaded task: do not turn a narrow task into architecture/protocol/migration work unless the task says so. Review-driven fixes must stay **in-scope blockers** (see `/cross_review` / `/code_review` scope governor). Follow-ups get a note, not silent scope expansion.
5. **Run the app (Principle 3 — after significant product change):**
   - Run **smoke** commands from `.agents/product_plugin.yaml` (or the product's documented health check).
   - Plus targeted unit/integration tests for the module under change (tooling from the product's stack).
   - **Behavior ≠ source:** green unit tests are not enough if runtime surface changed — smoke must pass.
6. **Validate (diff-first):**
   - `scripts/validate full` (and hygiene as needed)
   - Prefer: `python3 scripts/check_secrets_diff.py --base HEAD~1 --head HEAD` on code ships
   - If exit ≠ 0 → `❌ VALIDATION FAILED` and halt. Do NOT auto-fix.
7. **Mandatory `/code_review` closeout (soft auto — not optional for code ships):**
   1. Freeze scope:
      ```bash
      python3 scripts/review_scope.py --base <task-base> --head HEAD --json
      ```
   2. **Skip** full `/code_review` **only if** `skip_heavy_review` / `prose_only` is true
      (internal skill/docs notes only — not user-facing README/SECURITY/INSTALL).
      Record in handoff: `code_review: skipped (prose-only)`.
   3. **Otherwise MUST run `/code_review`** (same session is fine; prefer a **different
      model** when `CODE_REVIEW_MODEL` / `GROK_MODEL_CROSS_REVIEW` is set):
      - Write `.agents/artifacts/CODE_REVIEW.md` (marker `CODE-REVIEW`)
      - P0-first; scope governor; secrets scan
      - If accepted P0 remain → fix in-scope only, re-run focused tests + `/code_review` once
   4. Do **not** set pipeline phase here — still `/pr_review` later.
   5. Then continue with `/cross_review` when the diff is large or non-trivial (personas +
      obsolete scan). Small code ships: `/code_review` alone is the minimum; large diffs need both.
8. **Handoff:**
   - Mark product task ✅ in the product roadmap or harness item in `.agents/BACKLOG.md`
   - Update product workflow/drift docs if the product uses them
   - `scripts/pipeline_state set-phase ready_for_review --score <X>`
   - **Optional notes vault (unless ephemeral):**  
     `python3 scripts/sync_vault_devlog.py --note "<task title>" --bullet "…"`  
     Never raw-append; never hand-write a release `… synced` block (that is `/sync_docs` only).  
     Shape SoT: harness **`docs/dev-log.md`** (Option A: newest-first, UTC·HKT, release vs note).
   - Optional worksheet: `python3 scripts/generate_worksheet.py --task-id <id> --title "…"` → `.agents/traces/`
   - **Always** print the next skill as a single parseable line (and run the helper):
     ```bash
     python3 scripts/next_skill.py --after execute_dev --base <task-base> --head HEAD --verbose
     ```
     Example stdout (exactly one of these patterns):
     ```text
     NEXT_SKILL=/code_review
     NEXT_SKILL=/pr_review --validate
     ```
     Agents and humans must launch **that** skill next (no free-form “if needed”).
   - Output: `📦 READY FOR REVIEW.` + `code_review: required|skipped (prose-only)` + `NEXT_SKILL=…`  
   - Handoff must note **TDD proof**: which tests went red then green (or "docs-only, TDD N/A")
   - Prefer filling `PR_DRAFT.md` from harness `templates/PR_DRAFT.md`:
     **What Problem This Solves**, **Why This Change Was Made**, **User Impact**, **Evidence**,
     plus **Red-proof** (`red_cmd` / `green_cmd`) when TDD applies

**Timeout & Failure Handling:**
- If any step exceeds `timeout-seconds` → halt with `⏱️ TIMEOUT` and preserve partial artifacts
- If `scaffold_tests` fails → preserve generated test file for manual inspection
- If validation fails → preserve `PR_DRAFT.md` with failure details
- No automatic retries (per `max-retries: 0`) — human must fix and re-run

**Recovery Path (if blocked):**
- If `/pr_review` returns `blocked` → agent receives remediation steps in `PR_DRAFT.md`
- Agent runs `/execute_dev` again → pre-condition check passes (phase=`blocked`)
- Agent fixes only cited violations → re-validates → advances to `ready_for_review`
- No infinite loops: max 3 remediation cycles per task before human escalation
