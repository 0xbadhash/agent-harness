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
2. Write `.agents/artifacts/RETRO.md` (marker `RETRO`) with:
   - What went well
   - Failures / near-misses (with gate names)
   - **Harness improvements** (skills/scripts/docs)
   - **Product improvements** (tests/smoke/plugin)
   - Explicit non-actions
3. Optional vault note: `sync_vault_devlog.py --note "Retro …"`
4. Do **not** set `pipeline.json` phase.

## Handoff

```text
✅ RETRO DONE
NEXT_SKILL=(done)
```
