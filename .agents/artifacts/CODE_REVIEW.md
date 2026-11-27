# CODE-REVIEW — correction → check wiring

**Marker:** CODE-REVIEW

- Command: `python3 scripts/next_skill.py --after execute_dev --base origin/main --head HEAD`
- Base: `origin/main` · Head: `HEAD`
- Secrets scan: covered by `hard_gates` (`check_secrets_diff.py`)

## Standards

- `scripts/check_correction_checks.py` follows the existing `(ok, messages)` checker contract and stays dependency-free.
- `check_lint_ratchet.check` and `check_comment_audit.check` reuse existing helpers; no duplicated parsing logic beyond one shared `_findings_from_diff`.
- `hard_gates` adds three calls in the same guarded style as the rest of the pack; prose-only ships skip them explicitly.
- No P0 findings. One nit: the three new `try/except` blocks repeat the pack's established pattern; acceptable for consistency with 15 existing gates.

## Spec

- AC-1 through AC-4 are covered by `tests/test_lint_ratchet.py`, `tests/test_comment_audit.py`, `tests/test_correction_checks.py`, and `tests/test_hard_gates.py`.
- AC-5 is documentation in `skills/code_review/SKILL.md`; verified by reading the file and `verify_skills.py`.
- AC-6/AC-7 verified by the full suite (477 passed) and `smoke_unit.sh`.
- AC-8 is a `hard_gates` secret scan on the diff.
- Scope matches the spec. The prerequisite T2086U text commit is called out in the PR draft and adds no behavior.

## Correction checks

- Lint regression could bypass the local gate → tests/test_lint_ratchet.py
- New history comment could pass review → tests/test_comment_audit.py
- Review findings could stay prose-only → tests/test_correction_checks.py
- Gate wiring could silently skip code ships → tests/test_hard_gates.py

## Findings

- P0: none.
- Follow-ups: none required for this slice.

## Verdict

Approve. The change is local to the harness gate pack, all targeted tests went
red then green, and the full suite plus smoke are green.
