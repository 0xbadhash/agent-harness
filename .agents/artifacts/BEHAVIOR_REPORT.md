# Behavior report — T2088U harness wiring

**Marker:** BEHAVIOR-REPORT
**Contract:** `.agents/artifacts/BEHAVIOR_CONTRACT.md`
**Date:** 2026-11-27
**Method:** source-blind CLI runs; no implementation files were read to judge
pass/fail.

| Clause | Result | Evidence |
|--------|--------|----------|
| B1 ticket DAG | pass | `check_ticket_dag.py` → `rc=0`, 5 tickets, frontier `01, 02`; workflow tickets → 2 tickets, frontier `02` |
| B2 stack layers | pass | `stack_plan.py --json` → `layers=[['01','02'],['03','04','05']]`, chunks `[1, 2]` |
| B3 stack write | pass | `--write` created `.agents/artifacts/STACK_PLAN.md` and `.json` |
| B4 unknown dependency | pass | fixture with `**Blocked by:** 99` → `rc=1`, message names `99` |
| B5 retro issue bodies | pass | `--file-issues` → retro + `2026-11-27-tests.md` + `2026-11-27-umbrella.md` |
| B6 offline default | pass | `--gh` without `--file-issues` → `rc=2`; offline run made no subprocess call (test) |
| B7 spec gate | pass | ship spec → `rc=0`; colliding `policy_id` / `Policy ID` → `False` with both line numbers |
| B8 comment audit | pass | `check_comment_audit.py --diff 0336317...HEAD --strict` → clean |
| B9 smoke | pass | `product_smoke.py` → 2/2 steps green |

## Notes

- No UI or HTTP surface is involved; the contract covers CLIs and generated
  artifacts.
- B4 and B7 use throwaway directories under `/tmp`; the ship tree is unchanged.
- The workflow-harness ticket DAG check ran against the companion tree.

## Verdict

All 9 clauses pass. No blocked or failing clause.
