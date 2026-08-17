# PR Draft — skill portfolio slim

**Spec:** docs/specs/2026-08-15-skill-portfolio-slim.md  
**Version target:** 1.4.29  

## What Problem This Solves

Portable ship_skills listed thin overlapping skills (feedback, plan_backend, audit_repo, test_automation) and optional ops skills as required install noise.

## Why This Change Was Made

Operator direction: remove / demote / merge into stronger skills (`/spec`, `/night_shift`, `/sweep`, `/audit_harness`).

## User Impact

- Smaller required skill set after install  
- Products can `--delete-stale-skills` to prune removed skills  
- Roadmap-from-gap via `/spec`; suites via night_shift  

## Red-proof

- red_cmd: `python3 -c "import sys; sys.exit(1)"`
- green_cmd: `python3 scripts/verify_skills.py`

## Traceability

| AC | Evidence |
|----|----------|
| AC-1 | removed `skills/feedback`; `removed_portable_skills.txt`; verify_skills |
| AC-2 | demoted agent_transcript + session_viewer; `optional_skills.txt` |
| AC-3 | plan_backend removed; `/spec --roadmap-from-gap` in skills/spec/SKILL.md |
| AC-4 | test_automation removed; night_shift suite orchestration section |
| AC-5 | audit_repo removed; sweep + audit_harness policy-gap |
| AC-6 | ship_skills 14; `python3 scripts/verify_skills.py` |
| AC-7 | docs/skills-catalog.md README llm-bootstrap policy AGENT_* |

## Threat notes

- authz: N/A skill docs only  
- secrets: none  

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | pending validate |
| smoke | product_smoke |
| verify_skills | green |

## Things that look bad but are actually fine

1. session_viewer / agent_transcript still under skills/ — optional not removed  
2. audit_harness grows — intentional merge of policy-gap  
3. retrospect soft warning on AGENT_REFERENCE citation  
