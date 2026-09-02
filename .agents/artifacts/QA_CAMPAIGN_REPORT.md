# QA-CAMPAIGN-REPORT
**Marker:** QA-CAMPAIGN-REPORT  
**Verdict:** exhausted this tree honestly (not ≥200 — scale cannot sustain that)

## Executive summary
Agent-harness SoT after 1.4.40 portfolio install. Baseline smoke+unit green. Three real gate bugs in the 1.4.39/40 agent-config work; all fixed with regression tests. No app server, no Playwright surface, no 200-bug hunt without fabricating defects.

**found=3  fixed=3  residual=0 (in campaign scope)**

## Coverage
See inventory matrix. Skipped categories have no product surface (`traits.web=false`, no HTTP API, no DB).

## Residual risk
- Edit guard is git-diff based, not a host PreToolUse hook — agents can still edit `.env` if they never run the script.
- Agent-config evals are deterministic script evals, not LLM task evals.
- email-detach origin divergence was an ops leftover, not a harness bug.

## Re-run
```bash
python3 scripts/product_smoke.py --root .
python3 -m unittest tests.test_edit_guard tests.test_green_checkpoint -v
python3 scripts/run_agent_config_evals.py --root .
```

## §9
1. Did not invent 197 filler bugs — skill forbids it.
2. Did not start a web stack to force E2E.
3. Did not bump VERSION / tag (qa_campaign is not `/release_mgmt`).
