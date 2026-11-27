# Plan: Outstanding ops closeout (2026-11-27)

- **Proposal / decision:** `/opt/second-brain/vault/01-Projects/agent-harness/challenges/2026-11-27-challenge-outstanding-ops.md`; artifact `.agents/artifacts/CHALLENGE.md`
- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent

## Stack & constraints

- Python 3, systemd user units, tmux, git. No new timers or schedulers.
- Solo-operated box: no review SLA and no self-merge into the harness.
- No secrets printed; no changes to other products' checkouts beyond diagnosis.
- A gateway restart happens only while the chief is idle.

## Approach

Order by deadline, not by list position: Harrow before its next 09:00 UTC run, the
GLM timer before 16:00 UTC, retention before 20:30 UTC. Then the harness publish,
branch cleanup, and the two diagnoses. The passive proofs are checked after
00:05 UTC, with a rule that turns a failure into a bug instead of a watch.

## Architecture decisions

- Harrow keeps running as `debian`; the fix is an ownership guard around a
  redundant `chmod`, plus a warning so the anomaly stays visible.
- Retention gets one-time directory creation. No `sudo mkdir` inside the unit.
- The GLM flip is disabled only after a `--dry-run`; a dry-run failure means the
  script is broken, not that the timer should be silenced.
- The Playwright guard is not muted; its message is true until the watchlist branch
  state changes.
- No new observability plumbing: the digest is the observation, checked manually.

## File / surface map

| Area | Change |
|------|--------|
| `/home/debian/hermes/scripts/hub-daily-jobs-harrow.py` | `publish()` ownership guard + warning |
| `/var/backups/boxdrop-feeds` | one-time `install -d` as `debian` |
| `~/.config/systemd/user/hermes-glm-default-flip.timer` | `disable --now` after dry run |
| agent-harness `feat/auto-review-relay` | fast-forward main, rebase, push, PR |
| email-detach branches | delete merged local and remote branch |
| `~/watchlist` | read-only diagnosis |
| `/srv/boxdrop/out/SCORECARD-GROKBUILD-OPS-CLOSEOUT-2026-11-27.md` | new scorecard |

## Implementation sequence

1. **Harrow.** Patch `publish()`: skip `chmod` unless the caller owns the target,
   warn when skipped, and keep a genuinely unexpected `OSError` visible. Add a
   temp-directory test. Record the target's ACL/ownership. Next automatic proof:
   the 09:00 UTC run.
2. **GLM flip.** Run `hermes-glm-default-flip.py --dry-run`. If it exits 0 and
   reports a no-op, disable the timer and note the pin's evidence. If it fails,
   diagnose the model-json read before touching the timer.
3. **Retention.** `sudo install -d -o debian -g debian -m 0755
   /var/backups/boxdrop-feeds`, run the unit, check the journal.
4. **Harness publish.** `git pull --ff-only` on `main`, rebase
   `feat/auto-review-relay` onto `origin/main`, run `pytest tests/ -q`, push, open
   a PR. On conflict: abort, keep the branch, report the files.
5. **Branch cleanup.** Confirm `git diff 76e291f..b47d969` is empty; delete the
   local branch with `git branch -d` and the remote with `git push origin --delete`.
6. **Playwright guard.** Read the guard's latest output, confirm whether
   `fix/night-readiness-security-gate` is merged into watchlist `main`, list the
   dirty generated artifacts, and bring a recommendation. No checkout change.
7. **Old system units.** For `btc-stack-refresh`, `jasmine-publish`,
   `weekly-cyber-audit`: last result, last journal line, whether they ever ran.
   One scorecard row each.
8. **Scorecard.** Every item with outcome, evidence, and what stayed open.
9. **After 00:05 UTC.** Check the digest line, the relay log, and the fallback log
   for a live gate event. Any error reopens that item as a bug.

## Testing plan

- Harrow: unit test on the ownership guard; next scheduled run must exit 0.
- Retention: manual run exits 0, journal has no traceback.
- Harness: `pytest tests/ -q` green before push.
- Branch deletion: empty tree diff against the squash commit.
- Guard: `playwright-merge-guard.sh --dry` output recorded.
- Relay/fallback: log lines after the first real events, not a synthetic send.

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Rebase conflict on the harness branch | Abort, keep the branch, report conflicting files |
| GLM dry-run also fails | Treat as a broken script; fix or retire explicitly |
| Harrow fix cannot be proven before tomorrow | Temp-dir test today, scheduled run tomorrow |
| Watchlist diagnosis touches another product | Read-only commands; recommendation, no checkout |
| Digest or relay errors after midnight | Reopen as a bug; do not mark the watch complete |
| Gateway restart collides with a turn | Restart only when the log shows idle |

## Open questions

None blocking. The watchlist branch owner decision is an output of step 6, not an
input.
