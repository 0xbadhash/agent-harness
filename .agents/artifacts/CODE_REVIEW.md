# CODE-REVIEW — markdown escape-hatch audit

**Marker:** CODE-REVIEW

- Command: `python3 scripts/next_skill.py --after execute_dev --base origin/main --head HEAD`
- Base: `origin/main` · Head: `HEAD`
- Secrets scan: covered by `hard_gates` (`check_secrets_diff.py`)

## Standards

- `check_markdown_audit` follows the same `(ok, messages)` contract and
  `fail:`/`ok:` prefixes as the other gate modules.
- The comment audit keeps its existing API; `audit_paths` gained an optional
  `root` for stable relative names, and the baseline helpers are local.
- `check_stale_agent_config` imports the cap helper rather than duplicating the
  line count; the import failure is a named missing-check finding.
- `hard_gates` and `validate.py` use the same guarded-call style as the pack.
- No P0 findings.

## Spec

- AC-1 and AC-2 are covered by `tests/test_comment_audit.py`.
- AC-3 is covered by `tests/test_markdown_audit.py::TestAgentsBloat` and
  `::test_stale_agent_config_calls_bloat`.
- AC-4 and AC-5 are covered by `::TestDoNotEnforcement` and `::TestEscapeHatches`;
  the live tree passes.
- AC-6 is the `validate.py` run (8/8 gates).
- AC-7 is `tests/test_repo_hygiene.py::test_debug_tag_fails`.
- AC-8 is the full suite, smoke, and the diff secrets scan.
- Scope matches the spec. The three `## Do not` edits are the minimum to make the
  rule true; no unrelated prose was rewritten.

## Correction checks

- Justification prose could pass as a rule → tests/test_markdown_audit.py
- Legacy comment findings could block every ship → tests/test_comment_audit.py::test_baseline_ratchet
- AGENTS.md could grow unbounded → tests/test_markdown_audit.py::TestAgentsBloat
- A `## Do not` bullet could stay unenforced → tests/test_markdown_audit.py::TestDoNotEnforcement
- The hard_gates wiring could be silent → tests/test_hard_gates.py::test_markdown_audit_blocks_code_ship
- The DEBUG promise could stay fictional → tests/test_repo_hygiene.py::test_debug_tag_fails

## Findings

- P0: none.
- Follow-ups: the comment audit prints excess baseline keys without the offending
  line text; a later slice can include the line for faster triage.

## Verdict

Approve. The targeted tests went red first (missing module and missing class), then
green; the full suite, smoke, and validate are green.
