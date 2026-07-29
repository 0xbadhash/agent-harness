# Agent skill-conformance eval (C5)

**Status:** lightweight runner (v1.4.10+) — still **not** a full eval platform / LLM-as-judge.

## Goal

Measure whether the **harness tooling** agents rely on still behaves: NEXT_SKILL,
hard gates, pipeline state — without building multi-agent scoring dashboards.

## Runner (automated)

```bash
# Fast (no unittest subset)
python3 scripts/agent_eval_checklist.py --root . --skip-tests

# Default: also run unittest subset when tests/ present
python3 scripts/agent_eval_checklist.py --root .
```

Exit **0** only if all checks pass.

| Check | What |
|-------|------|
| pipeline_state | `scripts/pipeline_state.py get` |
| next_skill | `next_skill.py --after execute_dev` prints `NEXT_SKILL=` |
| hard_gates | `hard_gates.py --help` |
| unittest_subset | optional: test_fsm_conformance, test_hard_gates, test_next_skill |

## Manual / complementary checklist

| Check | How |
|-------|-----|
| Illegal phase blocked | Call skill docs; wrong-state scenarios in tests |
| Install verify | `bash install_into_product.sh … --verify` |
| Spec gate | `python3 scripts/spec_gate.py` |

## CI

`.github/workflows/daytime-gates.yml` runs the checklist (skip-tests or full).

## Out of scope (still)

- LLM-as-judge on full transcripts  
- Multi-agent scoring dashboards  
- Product domain E2E (use `/qa_campaign`)  
