---
name: retrospect
description: >
  Post-ship or post-night_shift retrospective: distill failure modes into
  harness/product backlog items. Writes RETRO.md artifact; does not advance
  pipeline. Use after /sync_docs, night_shift FAIL, or user says retrospect.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 600
---

# `/retrospect` — close the ADSLC learning loop (C1)

**Not** a ship phase. After ship or readiness fail, capture what to improve.

## Workflow

1. Read latest evidence:
   - `.agents/artifacts/NIGHT_SHIFT_REPORT.md` / `NIGHT_SHIFT_TODO.md`
   - `PR_DRAFT.md`, `RELEASE_RUNBOOK.md`
   - optional: `python3 scripts/night_shift_taxonomy.py`
1b. **Mechanical retro (deterministic, offline):**
   ```bash
   python3 scripts/retro_job.py --root .
   python3 scripts/retro_job.py --root . --file-issues
   ```
   - `--transcripts` renders the most recent local session as evidence and
     redacts secret-like lines before writing `SESSION_TRANSCRIPT.md`.
   - `--pr-comments <path>` reads a saved PR review-comment dump;
     `--fetch-pr-comments --pr <n>` fetches it with `gh` (operator approval).
   - `--file-issues` writes one issue body per cluster plus an umbrella body under
     `.agents/artifacts/issues/`.
   - `--gh` posts those bodies; run it only with the operator's explicit approval.
2. Write `.agents/artifacts/RETRO.md` (marker `RETRO`) with:
   - What went well
   - Failures / near-misses (with gate names); classify each first: **mechanical** violations (banned API, import shape, file-location, syntax) MUST become an automated linter/gate check, never prose in `AGENTS.md`; reserve prose only for genuine **judgement calls**.
   - **Harness improvements** (skills/scripts/docs)
   - **Product improvements** (tests/smoke/plugin)
   - Explicit non-actions
   - **Action class for every finding:** `fix-now` (a real bug), `add-gate` (a
     mechanical violation becomes a check), `add-test` (a missing regression
     test), `doc` (a doc correction), or `non-action` (accepted risk). An
     unknown class is rejected by `retro_job.py`.
3. Optional vault note: `sync_vault_devlog.py --note "Retro …"`
4. Do **not** set `pipeline.json` phase.

## Handoff

```text
✅ RETRO DONE
NEXT_SKILL=(done)
```
