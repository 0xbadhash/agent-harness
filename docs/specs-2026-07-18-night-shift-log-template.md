# Standardize vault `night-shift-log.md` (timeline + dual time + newest-first)

- **Product:** agent-harness (SoT for `/night_shift`; products receive via install)
- **Created:** 2026-07-18
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** `.agents/BACKLOG.md` / `CHANGELOG.md` Open work
- **Plan:** none (behavior change localized to log write/rotate; implementation notes below)
- **Tracker:** local
- **Constitution:** AGENTS.md + policy defaults (report-only night_shift; no auto-fix; no release/push)

## Problem Statement

Per-product vault logs under `01-Projects/<id>/night-shift-log.md` drifted:

- Some files have only a short intro + stacked reports; others have a **Timeline** table after rotate.
- Older report headers are **UTC-only**; newer ones are **UTC · HKT**.
- Operators cannot scan PASS/FAIL history at a glance when rotate has not run.
- Multi-product and rotate tooling parse `# Night shift readiness —` chunks inconsistently if the document shape varies.

Operators need one **canonical template** for every product log: minimum summary table at the top, full reports newest-first, dual clocks on every new entry.

## Solution

When night_shift finishes (and when logs are rotated), every `night-shift-log.md` looks like:

1. **Title** — `# <product_id> night-shift log`
2. **How to read** (short, fixed)
3. **Timeline** table — **newest row first**, oldest last; columns `When` | `Result`
4. Horizontal rule
5. **Full report bodies** — newest first, oldest last; each report dual-stamped

New runs **update the Timeline** and **prepend** the new full report. Archive/rotate must **preserve** this shape (not invent a second format).

### Canonical template (normative)

```markdown
# <product_id> night-shift log

Newest-first readiness reports (`/night_shift` harness SoT).
Each entry: **UTC · HKT**. Hard-stops: no release, no push, no product auto-fix.

## Timeline

| When                                        | Result |
| ------------------------------------------- | ------ |
| 2026-07-18 07:07 UTC · 2026-07-18 15:07 HKT | PASS   |
| 2026-07-18 06:36 UTC · 2026-07-18 14:36 HKT | FAIL   |
| 2026-07-17 12:10 UTC                        | PASS   |

---

# Night shift readiness — <product_id> — 2026-07-18 07:07 UTC · 2026-07-18 15:07 HKT

**When:** 2026-07-18 07:07 UTC · 2026-07-18 15:07 HKT
**Overall:** PASS (6/6 gates) · mode=`full` · product=`<product_id>`
**Repo:** `<absolute product root>`
**Hard-stops:** no release, no push, no product auto-fix
**SoT:** agent-harness `scripts/night_shift_readiness.py`

## Gates

| Gate | Result | Exit |
|------|--------|------|
| … | ✅ or ❌ | 0 or n |

## Failures (tails)

_None._
<!-- or ### <gate_name> fenced tails -->

## Recommendations

1. …

---

# Night shift readiness — <product_id> — …
…
```

### Timestamp rules

| Case | Format |
|------|--------|
| **New writes** | Always dual: `YYYY-MM-DD HH:MM UTC · YYYY-MM-DD HH:MM HKT` via existing `format_when_dual()` |
| **Legacy rows** | May be UTC-only in Timeline; do **not** invent HKT when rewriting history |
| **Timezone** | UTC wall + `Asia/Hong_Kong` (fallback fixed UTC+8) |

### Ordering

- Timeline: **newest → oldest** (top → bottom).
- Full report sections: **newest → oldest** (top → bottom).
- Matching: Timeline row 1 corresponds to the first `# Night shift readiness —` block after `---`.

### Report body (unchanged semantics)

Keep existing fields produced by `night_shift_readiness.py` report renderer:

- Header: `# Night shift readiness — {product_id} — {when_dual}`
- Meta lines: When, Overall (PASS/FAIL + gate counts), Repo, Hard-stops, SoT
- ## Gates table
- ## Failures (tails)
- ## Recommendations
- Trailing `---` between entries (optional after last)

## User Stories

1. As an **operator**, I open any product’s `night-shift-log.md` and see **PASS/FAIL history in one table** without scrolling full tails, so I know trend before reading failures.
2. As an **operator in HKT**, I see **both UTC and HKT** on every new run so I do not convert times mentally.
3. As **night_shift / rotate tooling**, I parse a **stable document shape** (timeline + readiness headers) so multi-product SUMMARY and archive logic stay reliable.
4. As a **product agent**, I rely on harness install only — I do not invent a per-product log format.

## Implementation Decisions

Surfaces (SoT: **agent-harness** only; reinstall products after ship):

| Surface | Behavior |
|---------|----------|
| `scripts/night_shift_readiness.py` → `prepend_night_shift_log` | Rebuild document from: fixed header + **Timeline** (merge prior rows + new PASS/FAIL) + all full reports (new report first). Do not strip Timeline when prepending. |
| Report renderer | Always dual-time headers (already mostly true). |
| `scripts/rotate_night_shift_logs.py` | After archive, rewrite using **same** template helpers (shared module or pure functions) so rotate ≠ divergent format. Timeline after rotate = full parsed history (newest first), then latest full body only *or* keep N full bodies (see clarify default). |
| `docs/night-shift.md` | Document the template + example. |
| Optional golden | `tests/` fixture for prepend rebuild / parse. |

**Recommended default for rotate (record as decision):**

- On PASS-triggered rotate: archive full file; live log keeps **Timeline of all known rows** + **only the latest full report** (matches current rotate intent: reduce FAIL spam).
- On every readiness run: live log keeps Timeline + **all full reports still in file** (prepend grows until rotate).

**Explicit non-goals:**

- Changing gate logic, smoke, or hard-stops.
- Auto-fixing FAIL products.
- Rewriting all historical vault archives under `_archive/`.
- Requiring HKT backfill for old UTC-only headers.

## Testing Decisions

- Unit-test pure helpers (no vault required):
  - `format_when_dual` shape includes `UTC` and `HKT`
  - Given existing log without Timeline, first prepend produces Timeline + report
  - Second prepend inserts new row at **top** of Timeline and new report **above** prior reports
  - Parse of multi-report body preserves PASS/FAIL pairs
  - Rotate rewrite uses same header strings (`# <id> night-shift log`, `## Timeline`)
- Manual: run readiness dry-run or one product with vault path and open vault log.
- Smoke: existing harness `product_smoke` + `pytest` still green.

## Acceptance Criteria

- [ ] Spec template above is the **only** live format written by harness readiness + rotate.
- [ ] Every new readiness write includes dual **UTC · HKT** on: Timeline row, report H1, `**When:**` line.
- [ ] Timeline is **newest-first**; full reports **newest-first**.
- [ ] Prepend **updates** Timeline (does not drop prior rows from the live file until rotate archives them).
- [ ] Rotate after PASS still archives bulk history and leaves Timeline + latest report in the **same** template (no “How to read / auto-rotated …” alternate schema unless folded into How to read as optional one-liner).
- [ ] `docs/night-shift.md` documents the template with a minimal example.
- [ ] Unit tests cover prepend merge + dual-time; harness pytest green.
- [ ] Products receive change via normal harness install (no per-product forks of log format).
- [ ] No secrets committed; night_shift remains report-only (no release/push).

## Out of Scope

- Changing `TODO.md` or kanban card format (except timestamps already dual if touched).
- Multi-product `SUMMARY.md` redesign (may keep current rebuild; optional follow-up to dual-stamp “When”).
- Migrating every product’s live log offline in this ticket (optional one-shot rebuild script **allowed** if cheap; not required if next prepend normalizes).
- UI / Obsidian plugins.

## Clarifications

### 2026-07-18 (from operator request + code survey)

- Q: Order of entries?
  - A: **Newest on top**, oldest on bottom — Timeline and full reports.
- Q: Dual timezone?
  - A: **UTC and HKT** on all new writes; legacy UTC-only rows may remain in Timeline as-is.
- Q: Minimum structure?
  - A: Title + Timeline table + full report stack (example structure provided by operator).
- Q: Where is SoT?
  - A: **agent-harness** `scripts/night_shift_readiness.py` (+ rotate); products get copies on install.
- Q: Full history always in live file?
  - A: Live file grows with prepend; **rotate** may compact to Timeline + latest full report after PASS (existing policy).

## Further Notes

**Current gap (evidence):**

- `prepend_night_shift_log` writes a short intro and prepends reports but **no Timeline table**.
- `rotate_night_shift_logs.py` builds a Timeline only on rotate and uses slightly different intro (“Append-only…”, “How to read”, “Timeline (auto-rotated …)”).
- agent-harness vault log already has dual-time reports but no live Timeline until rotate; watchlist has Timeline after rotate.

**Risks:**

- Naive string prepend can duplicate Timeline sections — rebuild from parsed chunks preferred.
- Very long FAIL spam still needs rotate; Timeline alone does not replace archive policy.

**Constitution:** Aligns with report-only night_shift; improves operator readability without product auto-fix.

## Handoff

- Next: `/execute_dev` in **agent-harness** against this spec (then install_into products / night_shift timer picks up SoT path as configured).
- Then: `/cross_review` (if non-trivial) → `/pr_review --validate` → `/release_mgmt` → `/sync_docs`
- Optional follow-up: one-shot vault normalize for all `01-Projects/*/night-shift-log.md`
