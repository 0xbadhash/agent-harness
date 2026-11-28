# CROSS-REVIEW

- **Scope:** `main..HEAD` on `fix/qa-campaign-2026-11-28` (`41 files changed, 1416 insertions, 221 deletions, 780 non_test_loc`; commits `886b422`, `4a6c95e`)
- **Secrets Scan:** `python3 scripts/check_secrets_diff.py --base main --head HEAD` → `✅ secret scan clean (main...HEAD)`
- **Blockers:** 0
- **Majors:** 0
- **Nits:** 1 (pre-existing `C901`/`BLE001` ruff findings in touched gate scripts)

## Personas

### Security Guru
- **Finding:** none. Path traversal checks in `scripts/spec_gate.py`, `scripts/check_outer_loop.py`, `scripts/harness_shared_gates.py`, and `scripts/vault_writer.py` use `.resolve()` + `.is_relative_to(...)` (closing sibling-prefix bypasses). `scripts/run_tickets.py` tokenizes `command` with `shlex.split` before placeholder substitution. `scripts/check_edit_guard.py`, `scripts/check_lockfile_audit.py`, `scripts/check_security_paths.py`, `scripts/compliance_engine.py`, and `scripts/hard_gates.py` fail closed on git/scanner errors. `scripts/openweb_chromium_launch.py` guards `os.chmod` with an ownership check (`st.st_uid == os.getuid()`). `scripts/challenge.py::call_agy` uses list-argv `subprocess.run` (`shell=False`) with `--disable-slash-commands`.

### Maintainability Expert
- **Finding:** none (1 nit: pre-existing `C901` complexity and `BLE001` warnings in `scripts/hard_gates.py`, `scripts/check_hardcodes.py`, `scripts/check_outer_loop.py`, `scripts/finish_ship.py`, `scripts/next_skill.py`, `scripts/ops_dashboard.py`, `scripts/run_ship_chain.py`, `scripts/vault_fs.py`, `scripts/rotate_night_shift_logs.py`). New helpers (`_is_git_repo`, `_resolve_spec_path`, `_walk_pkgs`, `_rounds_agy`, `_note_agy`) are small and single-purpose, and `scripts/cross_review_gate.py` cleanly threads `root` without breaking legacy callers.

### Obsolete / cleanup (scoped)
- **Tier A (dead/unused):** 0 (all added helpers and constants in `main..HEAD` are wired into their modules and covered by `tests/test_challenge.py`, `tests/test_enhancement_mechanisms.py`, and `tests/test_qa_campaign_group_{a,b,c,d}.py`).
- **Tier B/C:** 0 (`call_glm` and `call_deepseek` in `scripts/challenge.py` remain intentionally behind `--backend api`).

### Domain Specialist
- **Finding:** none. Night-shift parsers (`night_fail_remediate.py`, `night_shift_log.py`, `night_shift_morning_triage.py`, `night_shift_taxonomy.py`, `ops_dashboard.py`, `promote_night_fails.py`, `rotate_night_shift_logs.py`) handle `DEGRADED`, `RED_SUITE`, and `🟡` verdicts consistently. `scripts/fork_sync_bot.py` aligns `parse_counts` and `issue_body` with `git rev-list --left-right --count origin/main...main` `(behind, ahead)` order. `scripts/finish_ship.py` parses the `[ahead ..., behind ...]` status bracket rather than matching branch names. `scripts/challenge.py` uses `gemini-4-carbon-high` (round 1) and `gemini-4-hydrogen-high` (round 2).

## Things that look bad but are actually fine
1. `call_glm` and `call_deepseek` remain in `scripts/challenge.py` as the explicit `--backend api` fallback per spec.
2. `AGY_ACCOUNT = "jeanclaude.mansart@gmail.com"` in `scripts/challenge.py` is a non-secret account identifier, not a credential.
3. `scripts/ops_dashboard.py::collect_security` intentionally skips `.git` while still scanning `node_modules` for known malicious payload filenames (`setup.mjs`, `Math_Symbol.js`, `math_init.js`).
4. `scripts/hard_gates.py` retains `except Exception:  # pragma: no cover` blocks around individual gate runners so one crashing gate records a violation instead of aborting the remaining gate checks.
