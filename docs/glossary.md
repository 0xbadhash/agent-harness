# Glossary

Terms the harness uses with a specific meaning. Each row names the surface that
owns the behavior, so a reader can find the code or skill behind the word.

| Term | Definition | Owning surface |
|------|------------|----------------|
| Ship FSM | The ordered skill flow from spec to release, with deterministic next-step routing. | `scripts/next_skill.py`, `skills/` |
| Door | A two-way change is reversible; a one-way change needs a named human and a rollback plan. | `templates/PR_DRAFT.md`, `scripts/pr_validator.py` |
| Spec | The product intent, acceptance criteria, and grill answers for one ship. | `skills/spec/SKILL.md` |
| Plan | The technical how: data model, sequence, risks, and rollback. | `skills/spec/references/plan-template.md` |
| Ticket | One tracer bullet with a kind, blockers, touched areas, acceptance, and a session id. | `.agents/specs/<slug>/tickets/` |
| Hard gate | A fail-closed check that blocks a ship when its condition is unmet. | `scripts/hard_gates.py` |
| Soft gate | A check that reports a warning and leaves the phase unchanged. | `scripts/validate.py` |
| Waiver | A short-lived, logged exception to the spec or a gate. | `.agents/artifacts/WAIVER_LOG.jsonl` |
| Prototype | A throwaway variant used to settle a shape question; it is reference, never the implementation. | `.agents/prototypes/`, `scripts/check_prototype_fidelity.py` |
| Prototype use | The declaration that shipped code reimplemented a prototype against the real data model. | `templates/PR_DRAFT.md` |
| Glossary term | A domain noun with one definition and one owning surface. | `docs/glossary.md` |
| Collision | Two glossary rows whose normalized terms are equal. | `scripts/check_glossary.py` |
| Comment route | The disposition of an audited comment: delete, move to an ADR, move to a test name, or rewrite. | `scripts/check_comment_audit.py` |
| Comment finding | One line the audit flags, with a kind and a route. | `scripts/check_comment_audit.py` |
| Constraint comment | A comment that states a rule, race, or ordering requirement the code must preserve. | `docs/tdd.md` |
| Constraint waiver | A `waive:` reason that lets a constraint comment stay without a test name. | `scripts/check_comment_audit.py` |
| Prefactor ticket | A ticket that extracts or prepares a shared component before the feature ticket. | `scripts/check_ticket_dag.py` |
| Session | The executor identity recorded on a ticket and in `TICKET_RUNS.jsonl`. | `scripts/run_tickets.py` |
| Merge stack | The ordered list of PRs derived from ticket dependency layers. | `scripts/merge_stack.py` |
| Background merge | A detached merge run that writes a log and prints its pid. | `scripts/merge_stack.py` |
| Merge run | One invocation of the merge stack over the PRs in ticket order. | `scripts/merge_stack.py` |
| Retro | A ranking of failures, evidence gaps, and latency from run records. | `framework/retro.py`, `tools/weekly_retro.py` |
| Retro report | One dated markdown report per workflow written under `docs/retros/`. | `tools/weekly_retro.py` |
| Evidence pack | The commands and results that prove a ship's claims. | `PR_DRAFT.md` |
| Traceability | The mapping from each acceptance criterion to a test or artifact. | `PR_DRAFT.md` |
| Runner label | The `runs-on` value a workflow job asks GitHub to provide. | `scripts/check_workflow_runners.py` |
| Workflow job | One job entry under `jobs:` in a workflow file. | `.github/workflows/` |
| Gate finding | One violation reported by a checker, with the file and subject named. | `scripts/hard_gates.py` |
| Scorecard row | One ranked item with its verdict, evidence, and delta. | `/srv/boxdrop/out/` reports |
