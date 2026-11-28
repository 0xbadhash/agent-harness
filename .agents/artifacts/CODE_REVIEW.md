# CODE-REVIEW

- **Command / Scope:** `python3 scripts/review_scope.py --base main --head HEAD --json` (`41 files changed, 1416 insertions, 221 deletions, 780 non_test_loc`; commits `886b422` and `4a6c95e` on `fix/qa-campaign-2026-11-28`)
- **Secrets Scan:** `python3 scripts/check_secrets_diff.py --base main --head HEAD` → `✅ secret scan clean (main...HEAD)`
- **Comment Audit:** `python3 scripts/check_comment_audit.py` → 7 pre-existing findings in untouched lines; 0 in `main..HEAD`
- **P0 (Blockers):** 0
- **Follow-ups:** 1 (non-blocking: pre-existing `ruff` `C901`/`BLE001` warnings in modified gate scripts)

## Standards
- Path resolution in `scripts/check_outer_loop.py`, `scripts/spec_gate.py`, `scripts/harness_shared_gates.py`, and `scripts/vault_writer.py` uses `.resolve()` paired with `.is_relative_to(...)` instead of `str.startswith(...)`, preventing sibling-directory prefix bypasses.
- `scripts/run_tickets.py` runs `shlex.split(command)` before substituting `{ticket}` and `{worktree}` into `argv`, preventing spaces or shell metacharacters in interpolated values from altering tokenization.
- `scripts/challenge.py::call_agy` uses list-argv `subprocess.run` (`shell=False`), `--disable-slash-commands`, and `timeout=180`.
- Fail-closed git/subprocess handling in `scripts/check_edit_guard.py`, `scripts/check_lockfile_audit.py`, `scripts/check_security_paths.py`, `scripts/compliance_engine.py`, `scripts/hard_gates.py`, and `scripts/run_ship_chain.py`.
- `ruff check` on the 39 Python files in `main..HEAD` reports 32 pre-existing `C901` complexity and `BLE001` blind-except warnings (mostly `# pragma: no cover` gate wrappers in `scripts/hard_gates.py`); no new syntax, import, or security lint errors.

## Spec
- Covers `886b422` (`challenge` default `--backend agy` with `gemini-4-carbon-high` / `gemini-4-hydrogen-high` and `--backend api` fallback) and `4a6c95e` (`BUG-001` through `BUG-039` QA campaign fixes with regression tests `tests/test_qa_campaign_group_{a,b,c,d}.py`).

## Findings
- Accepted: none (0 P0 blockers; 1 non-blocking follow-up noted for pre-existing `C901`/`BLE001` lint debt in touched gate scripts)
- Rejected: none

## Correction checks

- none (no accepted P0 findings)

## Tests / Smoke Run
- `pytest -q tests/test_challenge.py tests/test_enhancement_mechanisms.py tests/test_qa_campaign_group_a.py tests/test_qa_campaign_group_b.py tests/test_qa_campaign_group_c.py tests/test_qa_campaign_group_d.py` → `71 passed in 8.37s`
- `python3 scripts/check_secrets_diff.py --base main --head HEAD` → `✅ secret scan clean (main...HEAD)`
