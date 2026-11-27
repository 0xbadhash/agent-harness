# Cross-review — T2088U harness wiring and stacked ships

**Marker:** CROSS-REVIEW
**Base:** `0336317`
**Head:** `HEAD`
**Scope:** `scripts/{stack_plan,retro_job,spec_gate}.py`, five skill files,
spec references, CI workflow, template, and tests.

## Security Guru

Findings: none.

- Ticket and glossary content is parsed with strict regexes; no `eval`, no shell
  interpolation, and no execution of file contents.
- `stack_plan` resolves the ticket directory through `load_tickets`, which reads
  only `*.md` under the supplied directory.
- `retro_job --gh` uses an argv list (`gh issue create --title … --body-file …`)
  and requires `--file-issues`; the default path makes no network call.
- No new secrets, credentials, or absolute host paths enter the tree.

## Maintainability Expert

Findings: none blocking.

Scoped obsolete/cleanup scan (touched paths + direct callers):

| Tier | Item | Evidence | Confidence |
|------|------|----------|------------|
| A | none | every new symbol is used by `main()` or a test | 0.9 |
| B | none | existing `_glossary_terms` still serves `check_glossary` | 0.9 |
| C | default LOC estimate 150 | `stack_plan.DEFAULT_ESTIMATE`; tickets can add `**Estimate:**` | 0.8 |

- Coupling stays one-way: `stack_plan` imports `check_ticket_dag`; the reverse
  import does not exist.
- The skill edits name exact commands, matching the scripts.
- No dead branches; no duplicated DAG parser.

## Domain Specialist

Findings: none.

- `/execute_dev` now owns ticket-DAG, stack-plan, smart-zone, and compact-safety
  checks at the stages where they apply.
- `/code_review` owns the comment audit and per-layer chunks.
- `/retrospect` and `/qa_campaign` keep issue creation offline by default.
- The spec rituals match the domain: why-first, pain ranking, `STOP`, and
  candidate-name scenarios.

## Intentional oddities

1. The CI ticket-DAG loop is a no-op in this repo because `.agents` is ignored
   here; product installs carry the tickets.
2. Issue bodies are written even when there are no clusters, so the umbrella is
   always a stable artifact.
3. `stack_plan` includes done tickets in layer 0 so the plan mirrors history.

## Verdict

Blockers: 0. Tier A obsolete items: 0. Proceed to behavior validation.
