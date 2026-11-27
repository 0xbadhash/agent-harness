# Auto-review relay — tell the CEO when a harness is blocked on an approval card

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** `.agents/BACKLOG.md` → Open work
- **Plan:** none — the build is one script, two units and three hook entries; slices are listed inline
- **Tracker:** local
- **Constitution:** email-detach `AGENTS.md` (harness SoT first) + policy defaults
- **Grill-me:** complete

## Problem Statement

A harness pane that raises an Auto-review card stops and waits. Today the only reliable signal is the end-of-job scorecard hook: it fires when a job finishes, not when a job is stuck. On 2026-11-21 and 2026-11-22 the CEO had to be told in chat that cards were up on `grok-build:5`, `:8` and `:10`, then send a stamped keystroke so the run could continue. If nobody looks at the pane, the job sits still for hours and nobody knows.

T2096U proved there is no mid-run hook: the scorecard hook fires only on end tags, and the pane-poll timer that could see a mid-run pane is disabled. The t2090u rule "relay Auto-review cards to Boss on Signal and OpenBot" was never implemented.

## Solution

When any agent pane raises an approval card, the CEO gets one short Signal line within seconds:

> `grok-build:10 grok — approval needed: Confirm HEAD and dirty state of both harness trees — Read: git log --oneline`

The same event is POSTed to Boss as `kind=auto-review-card`, so a dashboard can show a blocked job. If the same card is still up ten minutes later, one reminder follows. Nothing is ever typed into the pane; approval stays with the CEO.

## User Stories

1. As the CEO, I want a Signal line when a harness stops on an approval card, so that a blocked night job does not sit until morning.
2. As the CEO, I want the pane named (session:window) so that I can go straight to it and press the option myself.
3. As the CEO, I want the card title and the command being asked about, so that I can judge without opening the pane.
4. As the CEO, I want one reminder if the card is still up after ten minutes, so that a forgotten card does not disappear into scrollback.
5. As the CEO, I want no message when the card is answered, so that the channel stays quiet.
6. As the CEO, I want cards from every harness (grok-build, Claude Code, Hermes, antigravity, others) to reach me, so that coverage does not depend on which tool a job used.
7. As the operator, I want a kill switch and an hourly cap, so that a noisy pattern cannot flood the channel.
8. As the operator, I want a daily count line, so that a dead watcher shows up as zero rather than as silence.

## Implementation Decisions

**Detection.** Hybrid, per grill G1/A.

- Native attention hooks push the event: Grok `Notification` (`notification_type: permission_prompt`, plus tool name and input), Claude Code `Notification`. Each hook runs a one-line shell wrapper that pipes stdin to `auto-review-relay.py --hook --harness <name>`.
- A tmux watcher covers harnesses with no hook. It polls every 20 s, lists panes with `pane_current_command`, and skips the viewer pane and every harness already covered by a hook (`grok`, `claude`). Card match requires an option line (`2 Yes, proceed` / `1. Yes` / `y/n`) inside the last 30 captured lines, so prose never matches.

**Delivery.**

- Signal: `hermes send --to signal` with `HERMES_HOME` set to the chief-of-staff profile (home channel `CEO DM`), the same path `pilot-pane-poll-signal.py` uses. Body ≤ 300 chars, one line.
- Boss: `/usr/local/lib/pilot/boss_webhook_post.py --kind auto-review-card --payload-file … --marker …`, URL and key read from the existing secret files.

**Dedupe and reminder.** Key = `sha256(harness|session|window|pane|title|command)`. First sight → send, record `first_seen`. At `first_seen + 600 s`, re-capture the pane; if the title still shows, send exactly one reminder and set `reminded`. Card gone → drop the row, send nothing.

**Failure behaviour.** Fail quiet, per grill G5/A: capture, parse and POST errors go to `STATE/relay.log`; a global cap of 12 messages per hour drops the rest with `post=capped`; the digest line reports `seen / sent / errors` so zero traffic is visible.

**State and surfaces.**

- Script: `/opt/catalyxt/ops/auto-review-relay.py`; SoT copy in `agent-harness/deploy/auto-review-relay.py` plus the two unit files.
- State: `/var/lib/pilot/auto-review-relay/` (`state.json`, `relay.log`, `posted/`, `DISABLED`).
- Units (user): `auto-review-relay-watch.service` (long-running watcher) and `auto-review-relay-digest.timer` (08:00 HKT, one Signal line).
- Hook wrappers under `~/.grok/hooks/` and `~/.claude/settings.json`. Codex is deferred (see Out of Scope).

**Non-goals that affect the experience.** No approval from Signal, no keystroke ever, no OpenBot transport (no sender exists), no replacement of the end-of-job scorecard hook, no transcript or file contents in the message.

## Testing Decisions

- Behaviour at the message boundary, not internals: given a hook payload or a captured pane, exactly one message with the expected fields.
- Fixtures: real hook JSON for Grok `permission_prompt`, a Claude `Notification`, and two pane captures (Grok card, Claude card) under `tests/fixtures/auto_review/`.
- `--dry` prints the Signal line and webhook body and sends neither, so the suite never touches Signal or the webhook.
- Seam: `auto-review-relay.py` is a CLI; tests call it as a subprocess with `AUTO_REVIEW_STATE` pointed at a temp dir.
- Manual live check: POST one synthetic hook payload with `--dry` first, then once for real with a CEO stamp.
- Docs-only: TDD N/A.

## Acceptance Criteria

- [ ] A Grok `Notification` with `notification_type=permission_prompt` on a tmux pane produces one Signal line and one webhook POST with `kind=auto-review-card` within 5 s.
- [ ] Two hook fires for the same card produce exactly one message.
- [ ] A card still visible at +10 min produces exactly one reminder; a resolved card produces none.
- [ ] A pane fixture with no option line produces no message.
- [ ] Viewer pane `grok-build:12` never produces a message.
- [ ] A pane whose harness is already hook-covered is skipped by the watcher (no duplicate).
- [ ] The 13th message in an hour is dropped and logged `post=capped`.
- [ ] `touch STATE/DISABLED` → zero sends, one log line.
- [ ] No secret-shaped string and no absolute path reaches the Signal text.
- [ ] `grep` proves the relay contains no `tmux send-keys` and no approval action.
- [ ] Digest timer writes one line with `seen / sent / errors`.
- [ ] `agent-harness` smoke (`check_hardcodes`, unit) passes; no secrets committed.

## Out of Scope

- Approving or declining from Signal, Boss, or any remote surface.
- Replacing or re-enabling `pilot-pane-poll.timer` job-done detection.
- OpenBot relay.
- Harness-internal changes (Grok, Claude source or config beyond the hook entry).
- The Codex lane: no hook entry and no watcher coverage until its `notify` argv shape is confirmed.
- Multi-host rollout; this is pilot-vps first.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: When should a card produce a message — once on appearance, on appearance plus resolution, or appearance plus a reminder?
  - A: Once when a card first appears, one reminder if the same card is still up at 10 minutes, nothing on resolution.

### G2 Non-goal / kill
- Q: What must this never do, and what would make us kill it?
  - A: Never type into a pane and never approve. Kill it if false positives exceed six messages a day, because a noisy approval channel is worse than none.

### G3 Wrong product
- Q: Is this a Hermes feature, an email-detach feature, or box ops?
  - A: Box ops. Detection sits outside Hermes (tmux panes and harness hooks), and the pilot scripts already live in `/opt/catalyxt/ops/`. SoT copies go to `agent-harness/deploy/`, per the harness-first rule.

### G4 Cheapest alternative
- Q: Could re-enabling the paused pane-poll timer do this?
  - A: No. `detect.py` fingerprints end tags, so it sees finished jobs, not cards. Reusing its 3-minute poll would still miss a card that appears and is answered between ticks. The watcher here polls at 20 s and only for harnesses without hooks.

### G5 Abuse / failure
- Q: If the watcher breaks or a pattern goes noisy, loud or quiet?
  - A: Quiet. Errors to the state log, 12 messages an hour cap, and a daily digest line so a dead watcher reads as zero.

### G6 Verify
- Q: How do we prove it without waiting for a real card?
  - A: Real hook payload and pane fixtures through a `--dry` CLI seam, then one synthetic live POST with a CEO stamp. No test sends Signal.

### G7 Priority
- Q: Where in the queue?
  - A: P1. It blocks no release, but every night that a card sits unattended costs hours.

## Clarifications

### 2026-11-27
- Q: Any harness dropped for the first build?
  - A: Codex. It has neither a confirmed `notify` shape nor watcher coverage in slice 1–4; it comes back as a follow-up.
- Q: Which panes may raise a card message?
  - A: Every harness across sessions (grok-build, antigravity, Hermes, Claude Code, others; Codex deferred), classified by the hook or the pane foreground process. Viewer panes and plain shells are excluded.
- Q: What goes into the message?
  - A: session:window, harness, card title, and the command being asked about, each clipped to ~200 chars, token-shaped strings and absolute paths redacted.

## Further Notes

- Grok hooks are documented at `.grok/docs/user-guide/10-hooks.md`: `Notification` fires for `permission_prompt`, and the stdin envelope carries `notification_type` in both camelCase and snake_case.
- The pane `:12` is the herdr viewer and mirrors another pane; capturing it would double-report.
- Codex is deliberately out of the first build. When it returns, confirm its `notify` argv shape against the installed Codex; if it cannot carry the tool text, it falls back to the watcher.
- Existing precedent for the two transports: `/opt/catalyxt/ops/pilot-pane-poll-signal.py` (Signal) and `/usr/local/lib/pilot/boss_webhook_post.py` (Boss).

## Handoff

- **Slice 1 done (2026-11-27):** `deploy/auto-review-relay.py` (hook ingest, normalisation, redaction, dedupe, hourly cap, rendering, dry/real delivery, reminder sweep) with `tests/test_auto_review_relay.py` (13 passed) and `tests/fixtures/auto_review/`. Nothing installed on the box; no live send.
- Next: slice 2 hook wrappers (`~/.grok/hooks/`, Claude `Notification`), slice 3 tmux watcher, slice 4 units + digest, slice 5 dry run on the box.
- Then: `/cross_review` (if large) → `/pr_review` → `/release_mgmt` → `/sync_docs`
