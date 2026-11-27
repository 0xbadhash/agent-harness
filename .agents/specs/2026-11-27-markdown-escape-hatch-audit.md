# Markdown escape hatch: prose must name a check

- **Product:** agent-harness
- **Created:** 2026-11-27
- **Status:** ready-for-agent
- **Priority:** P1
- **Roadmap:** CHANGELOG.md → Open work
- **Plan:** `.agents/specs/2026-11-27-markdown-escape-hatch-audit-plan.md`
- **Tracker:** local
- **Constitution:** `.agents/policy/base_constraints.md` + workspace `AGENTS.md`
- **Grill-me:** complete

## Problem Statement

Agents write justifications into comments, skills, and `AGENTS.md`: “for now”,
“temporary”, “safe to ignore”. Those lines are not enforceable and the next agent
copies them as the established pattern. `AGENTS.md` had no hard line cap on this
branch, and `## Do not` bullets named no check, so the prohibition lived only in
prose. `check_comment_audit.py` was wired into `hard_gates` but not `validate.py`,
and it did not flag justification language.

## Solution

Extend the comment audit with an `escape_hatch` class, add a Markdown audit that
caps `AGENTS.md` at 250 lines and requires every `## Do not` bullet to name an
enforcing check, and wire both into `validate.py`. Whole-tree comment findings are
ratcheted by a baseline so the gate fails on new prose, not on the legacy set. The
`[DEBUG-` promise in `skills/diagnosing-bugs/SKILL.md` becomes a real check.

## Implementation Decisions

- `check_comment_audit.classify_comment` gains `escape_hatch`; a line that names
  `scripts/…`, `tests/…`, `check:_`, `/pr_review`, or `next_skill` passes.
- `--baseline` / `--update-baseline` add a per-`path::kind` ratchet; the harness
  baseline lives at `config/comment_audit_baseline.json`.
- New `scripts/check_markdown_audit.py` owns `check_agents_bloat(root, 250)` and
  `check(root)`; it scans `AGENTS.md`, `skills/*/SKILL.md` (SoT wins over
  `.agents/skills`), and `templates/*.md`.
- `check_stale_agent_config.check` calls `check_agents_bloat`.
- `hard_gates` adds `markdown_audit` for non-prose ships; `validate.py` runs both
  comment audit (baseline) and Markdown audit.
- `check_repo_hygiene` fails on `[DEBUG-…]` tags in Python files.
- Non-goals: rewriting every prose “Do not” in the repository, adding a prose
  linter for tables, or changing the TODO warning policy.

## Testing Decisions

- Unit tests cover each `escape_hatch` phrase, the check-reference exemption, the
  baseline ratchet, the 250-line cap, `## Do not` enforcement, and the DEBUG tag.
- A `hard_gates` test patches the Markdown audit to fail and asserts the
  `markdown_audit` violation.
- A live-tree test asserts `check(ROOT)` passes after the three `## Do not`
  sections name their checks.
- Commands: targeted pytest, full pytest, `product_smoke.py`, `validate.py full`.

## Acceptance Criteria

- [ ] AC-1: `classify_comment` returns `escape_hatch` for “for now”, “temporary”,
  “works around”, and “safe to ignore” comments; a line naming a check passes.
- [ ] AC-2: `--baseline` passes at the recorded floor and exits 1 when a known
  `path::kind` count rises; `--update-baseline` writes the floor.
- [ ] AC-3: `check_agents_bloat` fails above 250 lines, passes at 250, and skips
  when `AGENTS.md` is absent; `check_stale_agent_config.check` reports it.
- [ ] AC-4: every bullet under `## Do not` in `skills/*/SKILL.md` names an
  enforcing check; the live tree passes.
- [ ] AC-5: bullet rules with justification prose fail unless they name a check;
  table rows are not treated as rules.
- [ ] AC-6: `validate.py full` runs the comment audit (baseline) and the Markdown
  audit; both pass.
- [ ] AC-7: `check_repo_hygiene` fails on a `[DEBUG-…]` tag in a Python file.
- [ ] AC-8: full suite, smoke, and validate pass; no secrets in the diff.

## Out of Scope

- Rewriting `AGENTS.md` (it is absent from this repo; the cap applies to products).
- A prose style linter beyond justification phrases.
- Changing the existing ticket-less TODO warning.

## Grill-me

**Status:** complete
**Date:** 2026-11-27

### G1 Outcome
- Q: What changes for the operator?
  - A: New prose that justifies skipping a check now fails `/pr_review` and
    `validate.py` unless it names the check.

### G2 Non-goal / kill
- Q: Is this a repo-wide prose rewrite?
  - A: No. The baseline freezes legacy comment findings; only the three
    `## Do not` sections needed edits.

### G3 Wrong product
- Q: Could this block legitimate docs ships?
  - A: Prose-only ships skip the code gates; Markdown ships still get the
    `AGENTS.md` cap and `## Do not` rule, which is the intent.

### G4 Cheapest alternative
- Q: Could a lint rule do this?
  - A: No. Ruff does not read comment intent or skill Markdown; the check is the
    smallest deterministic unit.
