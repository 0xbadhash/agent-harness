# TDD in `/execute_dev`

Code changes use **Red → Green → Refactor**. This is step 3 of the skill—not optional prose.

## Sequence

| Step | Agent must | Fail closed |
|------|------------|-------------|
| **Red** | Add/extend tests that express the public contract | Tests **must fail** when run |
| Guard | If new tests pass immediately | `OVER-SPECIFICATION` — fix tests first |
| **Green** | Minimum implementation to pass | — |
| **Refactor** | Clean up; keep green | — |
| **Regression** | Targeted suite (+ product smoke if runtime) | — |

## Docs-only work

If the task has **no** behavior/code change:

- Skip Red/Green  
- Handoff must say **`TDD N/A (docs-only)`**  
- Silent skip of code work is a process failure  

## Stack independence

TDD is a **discipline**, not a framework:

| You use | Red example |
|---------|-------------|
| Any unit runner | Failing test file first |
| API contract tests | Assert status/body before handler exists |
| UI | Component or node test fails before markup fix |

The product plugin’s `test_runners` / `smoke` document *what* to run; the skill enforces *order*.

## Scaffold helper

```bash
python3 scripts/scaffold_tests.py --task "<name>" --module "<target>"
```

Then edit until Red is real, then implement.

## Handoff proof

`/execute_dev` completion must list:

- Which tests went red  
- Which command went green  
- Or explicit TDD N/A  

Optional **Red-proof** block in `PR_DRAFT.md` (template: `templates/PR_DRAFT.md`):

```text
red_cmd: <command that failed>
green_cmd: <command that passed>
```

`pr_validator` scores **`suite_green`** (suite passes), not red-first. Red-proof is process honesty for humans/agents.

## Related

- Skill: `skills/execute_dev/SKILL.md`  
- Policy: `policy/base_constraints.md`  
- Smoke: `scripts/product_smoke.py`  
