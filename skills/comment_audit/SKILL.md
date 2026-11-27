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
python3 scripts/check_comment_audit.py --path scripts/foo.py --strict

# Whole tree against the ratchet
python3 scripts/check_comment_audit.py --root . \
  --baseline config/comment_audit_baseline.json

# Comment-to-code ratio (evidence, not a target)
python3 scripts/check_comment_audit.py --ratio
```

## Reading a finding

| Kind | Fix |
|------|-----|
| `history` | delete it; the diff already records the change |
| `commented_code` | delete it; version control is the archive |
| `todo` | add an owner or issue (`TODO(name)`, `TODO: #123`) |
| `escape_hatch` | name the check or condition that bounds it, or fix the check |

## Handoff

```text
✅ COMMENT AUDIT: <n> finding(s), ratio <x.xx>
NEXT_SKILL=/code_review
```
