# agent-harness backlog

## Open work
### Auto-review relay — mid-run approval cards to Signal + Boss (2026-11-27)
Spec: `.agents/specs/2026-11-27-auto-review-relay.md`. When any harness pane raises an approval card, send one Signal line and one Boss POST (`kind=auto-review-card`); one reminder at 10 min; notify only, never a keystroke. Hybrid detection: native attention hooks (`Grok` `Notification`) plus a tmux watcher for the rest (including `claude` and `codex` under the single-writer rule). Status: installed 2026-11-27 10:24 UTC — watch service active, digest timer next 2026-11-28 00:00 UTC.

## Done
### [DONE] Night validate_full: mission-feeds registration and product label (2026-11-08)
### [DONE] Retire duplicate night-shift-readiness unit (2026-11-08)
### [DONE] Vault dev-log standard (newest-first, UTC+HKT) (2026-07-18)
### [DONE] Night shift dev-deps preflight (2026-07-18) v1.3.1
### [DONE] night-shift-log template (2026-07-18) v1.3.0
