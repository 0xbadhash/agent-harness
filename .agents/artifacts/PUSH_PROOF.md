# PUSH_PROOF

_Generated 2026-08-02 09:37 UTC by finish_ship.py_

**ok:** `False`
**phase:** `shipped`
**branch:** `main`
**dirty:** `True`
**remote_sync:** `ahead`
**tag_hint:** `False`

## NEXT_SKILL plan (run in order — agent executes skills)

1. `sync_docs (if not done)`
2. `git push origin HEAD --tags`

## Missing / blockers

- ❌ working tree dirty (commit or stash before push proof)
- ❌ local commits not pushed (git push)

## Notes

- VERSION=1.4.12 but tag v1.4.12 not found (ok if not yet released)
- ahead of origin — run git push for full closeout (or --require-push)

## Operator

```bash
python3 scripts/finish_ship.py
python3 scripts/finish_ship.py --require-push
# After each skill: python3 scripts/next_skill.py --after <skill>
```

This tool does **not** auto-invoke LLM slash skills.

