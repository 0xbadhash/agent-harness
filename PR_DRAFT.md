# PR Draft: Un-defer Codex and Claude Code lanes in auto-review relay

**Range:** `origin/main...HEAD`

**Spec:** `.agents/specs/2026-11-27-auto-review-relay.md`
**Plan:** `.agents/specs/2026-11-27-outstanding-ops-plan.md`
**Tickets:** `.agents/specs/2026-11-27-auto-review-relay/tickets`

## What Problem This Solves

Codex and Claude Code panes were previously marked deferred in the auto-review relay spec, and `STRONG_OPTION` in `deploy/auto-review-relay.py` did not match Codex's `›` (`U+203A`) selection glyph.

## Why This Change Was Made

Un-defers Codex and Claude Code under the single-writer tmux `--watch` rule (`HOOKED_HARNESSES = {"grok"}`), adds `›` support to `STRONG_OPTION`, and adds fixture-based tests (`tests/fixtures/auto_review/claude_card.txt`, `codex_card.txt`) proving `--watch --once --dry` detects both harnesses without duplicate-send risk.

## User Impact

- Operators receive Signal + Boss notifications when `claude` or `codex` tmux panes raise an approval card.
- Single-writer rule prevents duplicate hook+watcher sends (`HOOKED_HARNESSES` remains `{"grok"}`).

## Evidence

- `python3 -m pytest -q tests/test_auto_review_*.py` (`36 passed`)
- `python3 scripts/validate.py full`
- `python3 scripts/check_secrets_diff.py --base origin/main --head HEAD`

## Merge Danger

**Door:** two-way
**Blast Radius:** Low. One-character regex addition in `deploy/auto-review-relay.py` plus two fixture files, one test function, and spec/backlog doc updates.

## Threat notes

**Tags:** secrets, injection

- **Assets:** tmux pane capture text, Signal/Boss relay messages.
- **Abuse cases:** Secret leakage or false-positive spam from pane text. `redact()` strips tokens/paths and `--dry` prevents live sends in tests.
- **Boundaries:** No new hooks or network listeners; watcher-only single writer for `claude` and `codex`.

## Traceability

| AC | Test / command |
|----|----------------|
| AC-Claude/Codex watcher | `tests/test_auto_review_watch.py::test_detects_claude_and_codex_fixture_cards` |
| AC-Single writer | `tests/test_auto_review_watch.py::test_skips_hooked_shell_and_viewer_panes` |
| Smoke | `python3 scripts/validate.py full` |

## Red-proof

```text
red_cmd: git show origin/main:deploy/auto-review-relay.py | python3 -c "import sys; sys.exit(0 if '\u203a' in sys.stdin.read() else 1)"
green_cmd: python3 -m pytest -q tests/test_auto_review_watch.py
```

Red exits 1 on `origin/main` (prior to adding `›` to `STRONG_OPTION`). Green runs `tests/test_auto_review_watch.py` including `test_detects_claude_and_codex_fixture_cards`.

## Evidence pack

- `hard_gates`: `python3 scripts/hard_gates.py --diff origin/main...HEAD`
- `pytest`: `36 passed` on `tests/test_auto_review_*.py`
- `validate`: `python3 scripts/validate.py full`

## Things that look bad but are actually fine

1. `codex` CLI is not installed on this host (`codex: command not found`), so its card fixture is derived from recorded CLI prompt layout and tested via `AUTO_REVIEW_TMUX_FIXTURE`.
2. `HOOKED_HARNESSES` intentionally remains `{"grok"}` so `--watch` acts as the single writer for both `claude` and `codex`.
3. `.agents/artifacts/PORTFOLIO_INSTALL_REPORT.md` and `REMAINING.md` were updated during the `v1.5.1` portfolio rollout.
