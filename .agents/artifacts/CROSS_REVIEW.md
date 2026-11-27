# CROSS-REVIEW — correction → check wiring

**Marker:** CROSS-REVIEW

- Base: `origin/main` · Head: `HEAD`
- Scope: `scripts/check_correction_checks.py`, `scripts/check_lint_ratchet.py`, `scripts/check_comment_audit.py`, `scripts/hard_gates.py`, `skills/code_review/SKILL.md`, tests, plus the prerequisite T2086U skill-text commit.
- Blocker count: **0**

## Security Guru

- No auth, network, subprocess-with-input, or secret handling added. `git diff` and `ruff` run with fixed arguments; `base`/`head` come from the operator's diff range.
- Finding: none (blocker/major). Nit: the diff range is interpolated into a `git diff` argument list, not a shell string, so option injection is bounded by `git` parsing. Accepted as-is.

## Maintainability Expert

- New checker follows the established `(ok, messages)` contract and is independently importable.
- `check_comment_audit.check` shares `_findings_from_diff` with the CLI path; no duplicated parsing.
- Finding: none (blocker). Nit: the three `try/except` blocks in `hard_gates` repeat the pack's existing pattern; consistency wins over extraction at this size.

### Obsolete / cleanup (scoped)

Touched paths plus direct callers/callees only.

| Tier | Item | Confidence | Evidence |
|------|------|-----------|----------|
| A | none | — | `grep -rn "check_comment_audit\|check_lint_ratchet\|check_correction_checks"` shows only CLI, tests, and the new `hard_gates` calls |
| B | none | — | no superseded helper or duplicate gate remains |
| C | none | — | no dead branch in the new checker; all three findings classes are reachable from tests |

## Domain Specialist

- Harness domain: a fail-closed gate must name the fix and must not block prose-only ships. Both hold: messages include the heading or command, and the prose branch appends explicit skips.
- Finding: none (blocker). Note: products with an older `CODE_REVIEW.md` will fail once; the message states the required heading.

## Follow-ups (not ship-blockers)

- Consider folding the three new gate calls into a helper once a fourth whole-tree check appears.

## Verdict

No blockers. Proceed to behavior validation and `/pr_review --validate`.
