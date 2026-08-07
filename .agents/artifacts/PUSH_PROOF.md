# PUSH_PROOF

_Generated 2026-08-03 08:25 UTC by finish_ship.py_

**ok:** `False`
**phase:** `init`
**branch:** `main`
**dirty:** `True`
**remote_sync:** `ahead`
**tag_hint:** `True`

## NEXT_SKILL plan (run in order — agent executes skills)

1. `execute_dev`
2. `code_review`
3. `cross_review`
4. `behavior_validator`
5. `pr_review --validate`
6. `release_mgmt`
7. `sync_docs`
8. `git push origin HEAD --tags`

## Missing / blockers

- ❌ working tree dirty (commit or stash before push proof)
- ❌ local commits not pushed (git push)
- ❌ require-push: remote_sync=ahead

## Notes

- —

## Operator

```bash
python3 scripts/finish_ship.py
python3 scripts/finish_ship.py --require-push
# After each skill: python3 scripts/next_skill.py --after <skill>
```

This tool does **not** auto-invoke LLM slash skills.

