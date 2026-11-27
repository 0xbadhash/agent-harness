# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** prose that justifies skipping a check fails the local gate unless it names the check; `AGENTS.md` cannot grow past 250 lines
**Surface:** `scripts/check_comment_audit.py`, `scripts/check_markdown_audit.py`, `scripts/check_stale_agent_config.py`, `scripts/hard_gates.py`, `scripts/validate.py`, `scripts/check_repo_hygiene.py`

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 Escape-hatch comments fail | pass | `tests/test_comment_audit.py::TestJustificationAudit` covers four phrases plus the check-reference exemption. |
| 2 Baseline ratchet holds | pass | `--update-baseline` recorded 7 legacy findings; `--baseline … --strict` exits 0, and a new file raises the count and exits 1. |
| 3 AGENTS.md cap is real | pass | `TestAgentsBloat` checks 251 fails, 250 passes, absent skips; `check_stale_agent_config` reports the breach. |
| 4 `## Do not` bullets name checks | pass | The live tree passes `check(ROOT)`; the three edited sections cite `challenge.py`, `pipeline_state.py`, `check_secrets_diff.py`, `next_skill.py`, `check_hardcodes.py`, `check_dev_log_contract.py`, and `vault_schema_lint.py`. |
| 5 Gate wiring | pass | `tests/test_hard_gates.py::test_markdown_audit_blocks_code_ship`; `validate.py full` prints `check_comment_audit` and `check_markdown_audit` as passing gates. |
| 6 Debug tags fail | pass | `tests/test_repo_hygiene.py::test_debug_tag_fails`; the live tree prints no DEBUG findings. |

## Summary

- pass: 6 · fail: 0 · blocked: 0 · out_of_scope: 0
- NEXT_SKILL=/pr_review --validate
