# Plan — correction → check wiring (T2087U item 1)

- **Product:** agent-harness
- **Spec:** `.agents/specs/2026-11-27-correction-checks.md`
- **Status:** approved
- **Scope:** `scripts/`, `skills/code_review/SKILL.md`, tests

## Approach

Reuse the checks the repo already owns instead of adding new policy prose. The
lint ratchet and comment audit keep their CLI behavior and gain a shared
`check(root)` / `check(root, base, head)` entry point that returns the same
`(ok, messages)` contract as every other gate module. `hard_gates` calls those
entry points for non-prose ships, so `/pr_review --validate` fails on the same
evidence the CLI would produce. A new `check_correction_checks.py` reads the
closeout review artifact and requires one line per accepted finding.

## Architecture

- `scripts/check_lint_ratchet.py` owns baseline loading and ruff parsing;
  `check()` composes `load_baseline`, `run_ruff`, and `compare`.
- `scripts/check_comment_audit.py` owns comment classification; `_findings_from_diff`
  is shared by the CLI and `check()`, which audits only added lines.
- `scripts/check_correction_checks.py` owns the review-artifact contract: a
  `## Correction checks` section, one bullet per finding, arrow mapping to a
  check token or `no-check: <reason ≥10 chars>`, and `none` for an empty review.
- `scripts/hard_gates.py` imports the three checks inside the existing guarded
  blocks and appends `hard_gates: <name>` violations; prose-only ships record
  explicit skips.

## Failure behavior

A missing `ruff`, a failed `git diff`, a missing section, or an unmapped bullet
all fail closed with the command or heading that fixes it. There is no silent
skip for code ships.

## Risks

The main compatibility risk is an older product `CODE_REVIEW.md` without the new
section; the failure message names the heading. A second risk is running ruff on
large trees inside every local review; the ratchet already does that in CI and
completes in seconds here.

## Rollback

Revert the feature commit. The three checkers keep working from their CLIs; only
the `hard_gates` calls disappear.
