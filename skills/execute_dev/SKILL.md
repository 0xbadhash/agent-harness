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
1. **Load task:**
   - If user args specify a task → use that (acceptance must be clear).
   - Else product: first open priority item in the product roadmap file (see `product_plugin.yaml` → `product_roadmap`).
   - Else harness: first open row in `.agents/BACKLOG.md`.
   - If none → `✅ ROADMAP EMPTY.`
2. **Spec check:** Missing acceptance criteria → `🛑 SPEC MISSING.` and halt.
3. **TDD (mandatory for behavior/code changes) — Red → Green → Refactor:**
   1. **Red:** Add or extend failing tests that express the public contract *before* (or with) the first implementation edit.
      - Optional helper: `scripts/scaffold_tests.py --task "<name>" --module "<target>"` (adapt to product layout).
      - Use the product's test runners from `product_plugin.yaml` → `stack` / project conventions.
      - Pure docs/policy-only: skip Red/Green but say so in handoff (no silent skip of code paths).
   2. **Prove Red:** Run the new/changed tests — they **must fail**. If they pass → `❌ OVER-SPECIFICATION` / wrong test; fix tests first.
   3. **Green:** Implement the minimum to make those tests pass. One sub-task only.
   4. **Refactor:** Clean up with tests still green.
   5. **Regression:** Run targeted suite + product smoke (from `product_plugin.yaml`) when runtime surface changes.
4. **Implement constraints:**
   - **UI is allowed** when the product task is user-facing UI (use the product's own stack from `product_plugin.yaml`). Prefer progressive enhancement over unnecessary SPA rewrites unless the product already is an SPA.
   - Non-UI product work: APIs, services, CLIs, data paths as the product defines.
   - Harness-only changes stay under `.agents/` + `scripts/`.
   - Do not put harness backlog items into the product roadmap.
5. **Run the app (Principle 3 — after significant product change):**
   - Run **smoke** commands from `.agents/product_plugin.yaml` (or the product's documented health check).
   - Plus targeted unit/integration tests for the module under change (tooling from the product's stack).
6. **Validate (diff-first):**
   - `scripts/validate full` (and hygiene as needed)
   - If exit ≠ 0 → `❌ VALIDATION FAILED` and halt. Do NOT auto-fix.
7. **Handoff:**
   - Mark product task ✅ in the product roadmap or harness item in `.agents/BACKLOG.md`
   - Update product workflow/drift docs if the product uses them
   - `scripts/pipeline_state set-phase ready_for_review --score <X>`
   - **Optional notes vault (unless ephemeral):**  
     `python3 scripts/sync_vault_devlog.py --note "<task title>" --bullet "…"`  
     Never raw-append; never hand-write a release `… synced` block (that is `/sync_docs` only).
   - Optional worksheet: `python3 scripts/generate_worksheet.py --task-id <id> --title "…"` → `.agents/traces/`
   - Output: `📦 READY FOR REVIEW. Prefer /cross_review then /pr_review --validate` + vault status  
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
