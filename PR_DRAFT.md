# PR Draft — agent-config gates 1.4.39

**Spec waiver:** chore  
**Spec:** `.agents/specs/2026-09-02-agent-sdlc-gates.md`  
**Version target:** 1.4.39  

## What Problem This Solves
Stale agent config, late-only guards, extra loops after green, no evals when skills/AGENTS/gates change.

## Why This Change Was Made
Operator: implement ranked gaps 1–4, full FSM, then portfolio install. No product VERSION bumps.

## User Impact
- hard_gates fail on missing agent-config refs
- diffs cannot include `.env`/secrets; fix-tasks cannot rewrite tests
- after score ≥95 at this SHA, next_skill goes to release, not another polish loop
- CI runs frozen agent-config evals (no LLM)

## Red-proof
- red_cmd: `python3 -c "import tempfile,sys; from pathlib import Path; sys.path.insert(0,'scripts'); import check_stale_agent_config as s; td=Path(tempfile.mkdtemp()); (td/'scripts').mkdir(); (td/'scripts'/'next_skill.py').write_text('x'); (td/'AGENTS.md').write_text('python3 scripts/nope_missing.py\n'); ok,_=s.check(td); raise SystemExit(0 if ok else 1)"`
- green_cmd: `python3 -m unittest tests.test_stale_agent_config tests.test_edit_guard tests.test_green_checkpoint tests.test_agent_config_evals -v`

## Traceability
| AC | Test / smoke |
|----|--------------|
| AC-1 stale missing script fails | tests/test_stale_agent_config.py |
| AC-2 edit_guard .env and fix-task tests | tests/test_edit_guard.py |
| AC-3 green next_skill → release_mgmt | tests/test_green_checkpoint.py |
| AC-4 evals pass on SoT | tests/test_agent_config_evals.py |
| smoke | product_smoke + run_agent_config_evals.py |

## Threat notes
- authz: none
- secrets: edit_guard blocks secret paths in diffs
- abuse: extra polish after green is routed away, not a host kill-switch

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | pr_validator |
| unittest | stale / edit_guard / green / evals |
| validate | run_agent_config_evals.py |

## Things that look bad but are actually fine
1. Spec waiver chore while a spec file exists — outer_loop skip; grill is in the spec
2. Leftover MORNING_TRIAGE / NIGHT_SHIFT_* / ops_dashboard unstaged
3. No Claude Code PreToolUse — portable scripts are the pin
4. Night-bar 73c2221 stays unpushed
