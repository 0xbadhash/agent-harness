# 03 — Re-score and PR triage reports

**What to build:** two read-only reports. The scorecard re-checks all 50 items
against pinned commits and records a delta. The triage report gives each open PR
its supersession evidence and a close/revive recommendation.

**Kind:** docs
**Prefactor:** none
**Blocked by:** None
**Estimate:** 180
**Status:** ready-for-agent

- [ ] `SCORECARD-GROKBUILD-HARNESS-TOP50-RESCORE-2026-11-28.md` names both
      pinned commits in its header
- [ ] Every one of the 50 items has a verdict, evidence, and a delta against the
      2026-11-21 scorecard
- [ ] Where a runnable check exists, the report records the command and exit code
- [ ] Items that fail the release claim become follow-up drafts in the report
- [ ] `TRIAGE-PRS-2026-11-28.md` covers #40, #21, #19, and #5 with the file
      evidence that `main` already contains their change
- [ ] Neither report writes inside a repository
