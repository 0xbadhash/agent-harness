# PR Draft — P1–P3 skills + NEXT_SKILL handoff

**Date:** 2026-07-25  
**Version:** 1.3.7  

## What Problem This Solves
After execute_dev/code_review, next skill was ambiguous ("if needed"). P1–P3 openclaw-adjacent skills missing.

## Why This Change Was Made
- `next_skill.py` always prints one line `NEXT_SKILL=…`
- P1 behavior_validator, P2 handoff, P3 session_viewer + agent_transcript
- execute_dev/code_review/cross_review handoffs use the helper

## User Impact
Clear next slash command; optional black-box behavior check; handoff/session tools.

## Evidence
- unittest test_next_skill + review_scope + secrets  
- validate full 5/5  

## Things that look but are fine
1. behavior_validator is contract-first skill, not full openclaw isolation  
2. session_viewer is minimal HTML not full openclaw TS viewer  
3. NEXT_SKILL still agent-enforced  
4. Large→cross_review heuristic is file/LOC based  
5. Runtime heuristic may send pure-script tools to behavior_validator (acceptable)
