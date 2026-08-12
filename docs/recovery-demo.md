# Recovery demo (Tier B-2)

**Classification:** `recovery: resumable` (not proven-durable).

## What resumable means

1. `pipeline.json` is atomic (temp + rename via `pipeline_state.py`).
2. Artifacts under `.agents/artifacts/` are re-readable after host crash.
3. Agent re-enters via `next_skill.py` + `session_context.py` without inventing a new phase.

## What it is **not**

- Durable multi-host orchestration
- Automatic retry of failed network side effects
- Proven crash-consistency under power loss mid-write of non-FSM files

## Demo script

```bash
# From a product or harness root with pipeline state
python3 scripts/recovery_demo.py --root .
# Simulates: snapshot phase → write artifact → re-read → print resume skill
```

Exit 0 if phase round-trips and session_context/next_skill hints are printable.
