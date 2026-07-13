# Engineering Assurance
## Scope & Precedence
- Safety > convenience
- Validation gates > local assumptions
- This file wins in conflicts

## Core Principles
1. Test behavior, not just paths
2. Risk-based depth (Low/Med/High)
3. Validate contracts and invariants
4. Deterministic tests (mock externals, no timing)
5. Fail loudly, never silently
6. Graceful degradation with explicit ladder
7. Operator visibility = correctness
8. Security boundaries non-negotiable

## Type Safety
- Strict mode mandatory for new code
- Legacy migration: 2-week horizon per `# type: ignore` (or language equivalent)
- Track intentional debt in each change's §9 (no separate ARCHITECTURE_DEBT.md)

## Validation Gates
- Every `/execute_dev` must pass compliance engine
- `/pr_review` uses deterministic rubric (≥95% to pass)
- CI blocks merges on gate failures

## Definition of Done
- [ ] Behavior implemented per spec
- [ ] Tests at correct risk depth
- [ ] All gates pass (type/lint/test/coverage)
- [ ] Critical failures observable via structured logs
- [ ] Fallback behavior explicit + tested
- [ ] No silent failure paths
- [ ] §9 "Things that look bad but are actually fine" included
- [ ] This document still matches reality

## §9 Tech Debt Audit
- Every finding cites `file:line`
- "Things that look bad but are actually fine" section required (see base_constraints.md for schema)
- Risk-tagged [Critical/High/Med/Low]
