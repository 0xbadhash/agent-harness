# PUSH_PROOF

_Generated 2026-11-28 06:12 UTC by finish_ship.py_

**ok:** `False`
**phase:** `shipped`
**branch:** `main`
**dirty:** `True`
**remote_sync:** `ahead`
**tag_hint:** `True`

## NEXT_SKILL plan (run in order — agent executes skills)

1. `sync_docs (if not done)`
2. `finish_ship --require-push`

## Missing / blockers

- ❌ working tree dirty (commit or stash before push proof)
- ❌ require-push: cannot push/verify while dirty

## Notes

- —

## Operator

```bash
python3 scripts/finish_ship.py
python3 scripts/finish_ship.py --require-push
# After each skill: python3 scripts/next_skill.py --after <skill>
```

This tool does **not** auto-invoke LLM slash skills.

