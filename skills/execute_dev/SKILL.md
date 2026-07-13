---
name: execute_dev
description: Implement one product or harness task with mandatory TDD. Product UI allowed when scoped; harness tasks use .agents/BACKLOG.md.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
preserve-artifacts-on-failure: true
---
# Pipeline Reference: docs/ARCHITECTURE.md § Agentic Pipeline Flow
# Handoff Contract:
#   Reads: BACKEND_ROADMAP.md (product) or .agents/BACKLOG.md (harness), .agents/state/pipeline.json
#   Writes: task tracker + pipeline → ready_for_review
# Anti-patterns & §9: docs/AGENT_REFERENCE.md
# Boundary: docs/PRODUCT_BOUNDARY.md

When invoked with `/execute_dev`:
0. **Pre-condition Check:**
   - Read `.agents/state/pipeline.json`
   - If `phase` ∉ {`init`, `blocked`} → `🛑 WRONG STATE. Current: {phase}. Run /pr_review or /sync_docs first.` and halt.
   - If working tree dirty (`git status --porcelain` non-empty, ignore `__pycache__` if policy allows) → `🛑 DIRTY TREE. Commit or stash changes first.` and halt.
1. **Load task:**
   - If user args specify a task → use that (acceptance must be clear).
   - Else product: first open Shaping / P0–P1 in `BACKEND_ROADMAP.md`.
   - Else harness: first open row in `.agents/BACKLOG.md`.
   - If none → `✅ ROADMAP EMPTY.`
2. **Spec check:** Missing acceptance criteria → `🛑 SPEC MISSING.` and halt.
3. **TDD (mandatory for behavior/code changes) — Red → Green → Refactor:**
   1. **Red:** Add or extend failing tests that express the public contract *before* (or with) the first implementation edit.
      - Python: `scripts/scaffold_tests.py --task "<name>" --module "<target>"` then edit until the new tests fail for the right reason.
      - PHP: add/adjust PHPUnit under `migration/tests/` (or Node under `migration/tests/*.test.js` for desk JS).
      - Pure docs/policy-only: skip Red/Green but say so in handoff/worksheet (no silent skip of code paths).
   2. **Prove Red:** Run the new/changed tests — they **must fail**. If they pass → `❌ OVER-SPECIFICATION` / wrong test; fix tests first.
   3. **Green:** Implement the minimum to make those tests pass. One sub-task only.
   4. **Refactor:** Clean up with tests still green.
   5. **Regression:** Run targeted suite + (for product) `php bin/health.php` when runtime surface changes.
4. **Implement constraints:**
   - **Product UI is allowed** when the task is desk/watchlist UX (PHP SSR + local JS under `migration/`). No SPA/Bootstrap/CDN.
   - Backend/API/CLI for non-UI product work; harness-only changes stay under `.agents/` + `scripts/`.
   - Do not put harness ORCH items into product Shaping.
5. **Run the app (Principle 3 — after significant product change):**
   - `cd migration && php bin/health.php` → exit 0
   - Plus targeted suite: PHPUnit, `node migration/tests/…`, or pytest for the module under change
6. **Validate (diff-first):**
   - `scripts/validate full` (and hygiene as needed)
   - If exit ≠ 0 → `❌ VALIDATION FAILED` and halt. Do NOT auto-fix.
7. **Handoff:**
   - Mark product task ✅ in `BACKEND_ROADMAP.md` or harness item in `.agents/BACKLOG.md`
   - Update `WORKFLOW_DOCUMENTATION.md` DRIFT TRACKER when product-facing
   - `scripts/pipeline_state set-phase ready_for_review --score <X>`
   - **Obsidian (unless ephemeral):**  
     `python3 scripts/sync_vault_devlog.py --note "<task title>" --bullet "…"`  
     Never raw `cat >>` vault; never hand-write `… synced`. See `AGENTS.md` Option A.
   - Optional worksheet: `python3 scripts/generate_worksheet.py --task-id <id> --title "…"` → `.agents/traces/`
   - Output: `📦 READY FOR REVIEW. Prefer /cross_review then /pr_review --validate` + vault status  
   - Handoff must note **TDD proof**: which tests went red then green (or "docs-only, TDD N/A")

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
