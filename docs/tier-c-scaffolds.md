# Tier C scaffolds (1.4.28)

Optional / early maturity. Each has a script or doc entrypoint; none own multi-agent runtime.

| ID | Feature | Entry | Status |
|----|---------|-------|--------|
| C1 | Agent harness micro-benchmark | `scripts/benchmark_harness.py` | scaffold |
| C2 | Eval checklist hook | `scripts/agent_eval_checklist.py` + this doc | existing + pin |
| C3 | SBOM / signing checklist | `scripts/check_sbom_signing.py` | warn-only |
| C4 | Sandbox policy notes | `docs/sandbox-policy.md` | doc |
| C5 | Telemetry events (local JSONL) | `scripts/telemetry_emit.py` | opt-in |
| C15 | Multi-agent runtime | — | **NON_GOAL** (see `harness.manifest.yaml` `non_goals`) |

## NON_GOAL: multi-agent runtime (C15)

agent-harness will **not** build an in-process multi-agent orchestrator, message bus, or shared memory runtime. Hosts (Grok, Cursor, Claude Code) own agent loops. Portfolio coordination stays kanban + night shift + OPS.
