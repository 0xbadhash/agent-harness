# CODE-REVIEW

- **Command / Scope:** `python3 scripts/review_scope.py --base origin/main --head HEAD --json` (1 line in `deploy/auto-review-relay.py`, 2 fixtures, 1 test, spec/backlog/PR_DRAFT)
- **Secrets Scan:** `python3 scripts/check_secrets_diff.py --base origin/main --head HEAD` → clean
- **Comment Audit:** `comment ratio: 1187 comment / 35699 code lines = 0.03`; `--strict` clean
- **P0 (Blockers):** 0
- **Follow-ups:** 0

## Standards
- Regex `STRONG_OPTION` in `deploy/auto-review-relay.py` extended by 1 character (`›`) to match Codex selection prompts; no duplicated logic, no blind exceptions added, no shell interpolation.
- Fixture tests in `tests/test_auto_review_watch.py` load `claude_card.txt` and `codex_card.txt` from `tests/fixtures/auto_review/`.

## Spec
- Matches `.agents/specs/2026-11-27-auto-review-relay.md` single-writer rule: `HOOKED_HARNESSES = {"grok"}` keeps `--watch` as the sole writer for `claude` and `codex` panes.

## Findings
- Accepted: none
- Rejected: none

## Correction checks

- none (no accepted findings)

## Tests / Smoke Run
- `python3 -m pytest -q tests/test_auto_review_*.py` → `36 passed`
- `python3 scripts/validate.py full` → `9/9 gates passed`
