# BEHAVIOR-REPORT

**Marker:** BEHAVIOR-REPORT
**Contract:** unset vault must refuse before a model call; night-shift smoke must stay green when `PRODUCT_VAULT_ROOT` is set
**Surface:** `scripts/challenge.py` CLI and `scripts/product_smoke.py`

## Results

| Clause | Status | Evidence |
|--------|--------|----------|
| 1 Unset vault, no `--vault` | pass | `env -u PRODUCT_VAULT_ROOT .venv/bin/python scripts/challenge.py --proposal <tmp>/p.md --decision <tmp>/d.md --root <tmp>` exited 1. stderr: `pre-flight failed, no model was called: vault root is unset; pass --vault or set PRODUCT_VAULT_ROOT`. stdout empty. |
| 2 Night-shift unit smoke with vault env set | pass | `PRODUCT_VAULT_ROOT` set to a temp dir. `scripts/product_smoke.py --root .` printed `smoke:hardcodes exit=0` and `smoke:unit exit=0`. `2 smoke step(s) passed`. |
| 3 Live model call | out_of_scope | No API key used. The refusal path returns before a model call. |

## Summary

- pass: 2 · fail: 0 · blocked: 0 · out_of_scope: 1
- NEXT_SKILL=/pr_review --validate
