---
name: comment_audit
description: >
  Audit comments for history, dead code, ownerless TODOs, and unbounded escape hatches, and report the comment ratio. Use for /comment_audit, "audit comments", or when code review needs the comment metric.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 300
---
# Reads: source files, `.agents/policy/comment-policy.md`
# Writes: findings to stdout, optional baseline JSON
# Anti-patterns: policy/AGENT_REFERENCE.md

## Policy

`.agents/policy/comment-policy.md` is the source of truth. Phase 1 covers
`scripts/` and `skills/`.

## Commands

```bash
# Added lines in a ship diff (fail closed)
python3 scripts/check_comment_audit.py --diff origin/main...HEAD --strict

# A single file or a short list
python3 scripts/check_comment_audit.py --path scripts/<file>.py --strict

# Whole tree against the ratchet
python3 scripts/check_comment_audit.py --root . \
  --baseline config/comment_audit_baseline.json

# Comment-to-code ratio (evidence, not a target)
python3 scripts/check_comment_audit.py --ratio

# Route every finding to one of four dispositions
python3 scripts/check_comment_audit.py --diff origin/main...HEAD --classify

# Fail a constraint comment with no test name, check reference, or waiver
python3 scripts/check_comment_audit.py --path scripts/<file>.py --constraints
```

## Reading a finding

| Kind | Fix |
|------|-----|
| `history` | delete it; the diff already records the change |
| `commented_code` | delete it; version control is the archive |
| `todo` | add an owner or issue (`TODO(name)`, `TODO: #123`) |
| `escape_hatch` | name the check or condition that bounds it, or fix the check |

## Routes

`--classify` prints one route per finding:

| Route | When | Action |
|-------|------|--------|
| `delete` | history or commented-out code | remove the comment |
| `move-to-ADR` | decision language: *chose*, *trade-off*, *rationale*, *alternative* | record the decision in `.agents/decisions/`, leave a pointer |
| `move-to-test-name` | constraint language: *must*, *never*, *before*, *order*, *invariant* | rename the test to state the constraint and assert it |
| `rewrite` | ownerless TODO or an unbounded escape hatch | state the owner, check, or condition |

A constraint comment keeps its place only when it names a test (`test_*`), a
check (`scripts/…`, `check:_`), or a waiver (`waive: <reason>`). `--constraints`
enforces that rule and exits 1 on an unbounded constraint.

## Approval

Routes change shipped code. Apply deletes, ADR moves, and test renames only
after the operator approves the plan in `/code_review`; put the approval line in
the handoff. A `rewrite` that only tightens wording needs no separate approval.

## Handoff

```text
✅ COMMENT AUDIT: <n> finding(s), ratio <x.xx>
routes: <delete n> / <move-to-ADR n> / <move-to-test-name n> / <rewrite n>
approval: operator-approved | pending
NEXT_SKILL=/code_review
```
