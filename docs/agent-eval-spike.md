# Agent skill-conformance eval (C5 spike)

**Status:** spike / P2 — not a hard ship gate.

## Goal

Measure whether agents **follow** harness skills (NEXT_SKILL, hard gates, phases)
without building a full eval platform.

## Minimal checklist (manual or scripted later)

| Check | How |
|-------|-----|
| Illegal phase blocked | Call skill docs; run `pipeline_state` wrong-state scenarios in tests |
| NEXT_SKILL after execute_dev | `python3 scripts/next_skill.py --after execute_dev` |
| Hard gates fail closed | `tests/test_hard_gates.py` |
| Install verify | `bash install_into_product.sh … --verify` |
| Spec gate | `python3 scripts/spec_gate.py` |

## Automated today

Harness CI / local:

```bash
python3 -m pytest tests/test_fsm_conformance.py tests/test_hard_gates.py tests/test_next_skill.py -q
```

## Future (out of scope for this spike)

- LLM-as-judge on full transcripts
- Multi-agent scoring dashboards
