# Plan — Operator start-feature front door

**Spec:** `.agents/specs/2026-07-29-operator-start-feature-front-door.md`

## How

| Piece | Approach |
|-------|----------|
| Doc | New `docs/start-a-feature.md` — copy operator guide already used in chat; link hard gates table |
| Links | README “Quickstart” + “Ship flow”; llm-bootstrap §3; AGENTS.harness template |
| Script | `scripts/start_feature.py --slug NAME [--title …] [--waiver …] [--write-spec-stub] [--root .]` |
| Spec stub | Minimal markdown: Problem/Solution/Acceptance checkboxes empty + status draft |
| PR_DRAFT | If missing, seed from `templates/PR_DRAFT.md` with Spec line filled |
| Install | Add `start-a-feature.md` to docs copy loop in `install_into_product.sh` |
| Tests | `tests/test_start_feature.py` temp dir |

## Non-goals

No UI, no FSM change, no network.

## Verify

```bash
python3 scripts/start_feature.py --root /tmp/t --slug demo --write-spec-stub
python3 scripts/spec_gate.py --root /tmp/t
python3 -m pytest tests/test_start_feature.py -q
```
