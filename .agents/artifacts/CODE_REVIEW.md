# CODE-REVIEW

**Marker:** CODE-REVIEW  
**When:** 2026-08-10  
**Scope:** HSQ-2 items 1–9 (FSM transitions, auto-markers, CI filter, vault defaults, protect playbook, OPS waiver+JSONL, CODE-REVIEW floor, skip-hard-gates log)

## Findings
- FSM ALLOWED_TRANSITIONS forbids init→shipped without force; force logs FORCE_TRANSITION_LOG.
- run_ship_chain auto markers require --allow-auto-markers; quality floor rejects thin auto stubs.
- CI skill-conformance skips when no skill-relevant paths on PR (main/dispatch still run).
- Vault hardcoded /opt is last-resort with warn; PRODUCT_VAULT_ROOT preferred.
- Protect-list merge playbook documented.
- OPS-DASHBOARD shows 30d waiver summary; OPS_SNAPSHOTS.jsonl appended.
- skip-hard-gates writes SKIP_HARD_GATES_LOG.jsonl.

## Verdict
Approve for merge after unit tests and validate full green.
