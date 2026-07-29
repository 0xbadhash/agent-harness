# Plan — Hard gates pack

## Stack

Python 3, existing `pr_validator`, `review_scope`, `check_secrets_diff`, unittest/pytest.

## Modules

| File | Role |
|------|------|
| `scripts/hard_gates.py` | `evaluate()` → violations list + ok bool |
| `scripts/pr_validator.py` | Call evaluate; rubric hard_gates=25 |
| `tests/test_hard_gates.py` | Unit matrix |
| `docs/ship-flow.md` | Hard gates section |
| `skills/pr_review/SKILL.md` | Document hard gates |

## Rubric (100)

| Bucket | Points |
|--------|--------|
| suite_green | 20 |
| gate_clean | 20 |
| section_9 | 15 |
| no_hardcode | 10 |
| pr_hygiene | 10 |
| hard_gates | 25 |

## Detection helpers

- Prose-only: `review_scope.build_baseline` + `should_skip_heavy_review`
- Runtime: reuse `next_skill._runtime_surface` or duplicate thin heuristic in hard_gates to avoid circular imports
- CODE-REVIEW: file `.agents/artifacts/CODE_REVIEW.md` contains `CODE-REVIEW` or `**Marker:** CODE-REVIEW`
- BEHAVIOR: `.agents/artifacts/BEHAVIOR_REPORT.md` contains `BEHAVIOR-REPORT`
- Red-proof: PR_DRAFT matches `(?i)red.?proof|red_cmd|green_cmd|TDD` + evidence of tests, OR explicit `TDD N/A` / `docs-only`
- Spec: `(?i)\*\*Spec:\*\*` path or `(?i)\*\*Spec waiver:\*\*\s*(hotfix|chore|docs-only|prose-only)`

## CLI

`pr_validator.py --diff A...B` unchanged; add `--skip-hard-gates` for emergencies (document; still warn).
