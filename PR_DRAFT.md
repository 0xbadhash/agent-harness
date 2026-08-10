# PR Draft — HSQ-2 Integrity & Ops (1–9)

**Spec:** `.agents/specs/HSQ-2-integrity-ops.md`  
**Version:** 1.4.21

## What Problem This Solves

Audit findings: FSM transitions unenforced; auto-marker ship chain gameable;
CI path filter cosmetic; vault /opt defaults; protect-list ops undocumented;
waivers/ops lack trends; CODE-REVIEW marker-only; skip-hard-gates silent.

## Why This Change Was Made

HSQ-2 recommendations 1–9 from deep audit — enforce integrity before more features.

## User Impact

- Illegal phase jumps fail unless forced and logged
- Auto ship chain requires explicit --allow-auto-markers
- Skill CI skips non-skill PRs
- Vault prefers PRODUCT_VAULT_ROOT
- OPS shows waivers + JSONL snapshots
- Thin CODE-REVIEW fails hard_gates
- skip-hard-gates is audited

## Evidence

- pytest tests/ green
- hard_gates ok with quality floor
- validate full

## Spec / waiver

**Spec:** `.agents/specs/HSQ-2-integrity-ops.md`

## Traceability

| AC | Test |
|----|------|
| AC-1 transitions | tests/test_pipeline_transitions.py |
| AC-8 CODE-REVIEW floor | tests/test_hard_gates_quality.py |
| AC-2–7,9 | code + docs + CI YAML |

## Red-proof

- red_cmd: pre-change pytest
- green_cmd: pytest tests/ -q

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | ok |
| smoke | product_smoke |
| pytest | unit suite |
| validate | full |

## Threat notes

- Force-transition and skip-hard-gates logs can identify operators (username) — low sensitivity
- Auto-marker path still not a substitute for human review

## Things that look bad but are actually fine

1. init→approved allowed for score-without-ready stamp (documented)
2. /opt vault still last-resort if directory exists (warn only)
3. Protect playbook is docs-only (no auto-merge)
