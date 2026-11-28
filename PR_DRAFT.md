# PR Draft: Auto-review relay, Hermes billing-only fallback gate, and ops closeout plan

**Range:** `origin/main...HEAD`

**Spec:** `.agents/specs/2026-11-27-auto-review-relay.md`
**Plan:** `.agents/specs/2026-11-27-outstanding-ops-plan.md`
**Tickets:** `.agents/specs/2026-11-27-auto-review-relay/tickets`

## What Problem This Solves

Grok approval cards in tmux panes could stall unattended overnight runs without notifying the operator, and Hermes fallback routing could trigger on non-billing errors. Additionally, outstanding ops closeout items needed a deadline-ordered plan.

## Why This Change Was Made

Adds a deterministic tmux/hook-based auto-review relay (`deploy/auto-review-relay.py`), systemd units (`deploy/auto-review-relay-watch.service`, `deploy/auto-review-relay-digest.{service,timer}`), a hook wrapper (`deploy/hooks/grok-auto-review-relay.sh`), a billing-only gate patch for Hermes (`deploy/patches/hermes-fallback-when.patch`), and the ops closeout plan.

## User Impact

- Operators receive Signal notifications for Grok approval cards and a daily `00:00 UTC` digest line.
- Hermes fallback lane triggers only on billing/credits errors.
- No changes to existing harness core gates; all additions live under `deploy/`, `.agents/specs/`, and `tests/`.

## Evidence

- `python3 -m pytest tests/ -q` (`619 passed, 3 skipped, 11 subtests passed`)
- `python3 scripts/validate.py full` (`9/9 gates passed`)
- `python3 scripts/check_secrets_diff.py --base origin/main --head HEAD` (clean)
- `python3 deploy/auto-review-relay.py --digest --dry` (exit 0)

## Merge Danger

**Door:** two-way
**Blast Radius:** Low. Additive `deploy/` scripts, systemd unit templates, patch file, specs, and unit tests. Reverting removes the new `deploy/` and `tests/test_auto_review_*.py` files cleanly.

## Threat notes

**Tags:** secrets, subprocess

- **Assets:** Signal notification target, tmux pane text, hook JSON payloads.
- **Abuse cases:** Secret leakage from pane text or crafted hook JSON causing shell injection. Subprocess calls use argument lists without shell interpolation, and secrets scan is clean.
- **Boundaries:** No new network listeners; `--dry` flag prevents live Signal sends during tests.

## Traceability

| AC | Test / command |
|----|----------------|
| AC-1 | `tests/test_auto_review_relay.py` |
| AC-2 | `tests/test_auto_review_watch.py` |
| AC-3 | `tests/test_auto_review_hook_wrapper.py` |
| AC-4 | `tests/test_auto_review_units.py` |
| Smoke | `python3 deploy/auto-review-relay.py --digest --dry`, `python3 scripts/validate.py full` |

## Red-proof

```text
red_cmd: git cat-file -e origin/main:deploy/auto-review-relay.py
green_cmd: python3 -m pytest tests/test_auto_review_relay.py tests/test_auto_review_watch.py tests/test_auto_review_units.py tests/test_auto_review_hook_wrapper.py -q
```

Red exits 128 on `origin/main` because `deploy/auto-review-relay.py` does not exist on the base. Green runs the four auto-review test suites.

## Evidence pack

- `hard_gates`: run via `python3 scripts/hard_gates.py --diff origin/main...HEAD`.
- `pytest`: `619 passed, 3 skipped, 11 subtests passed in 52.61s`.
- `validate`: `python3 scripts/validate.py full` → `9/9 gates passed`.

## Things that look bad but are actually fine

1. `deploy/patches/hermes-fallback-when.patch` is stored as a patch under `deploy/patches/` because `hermes-agent` lives in a separate repository.
2. `deploy/auto-review-relay.py` uses `--dry` for CLI verification so dry runs never send live Signal messages.
3. `.agents/specs/2026-11-27-outstanding-ops-plan.md` is included in this branch as the post-challenge closeout plan for the ops items.
