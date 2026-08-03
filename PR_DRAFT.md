# PR Draft — detailed ship flow docs (v1.4.14)

**Range:** 38c0d19..HEAD  
**Spec waiver:** docs-only

## What Problem This Solves
Operators and LLMs lacked one detailed map of skills, hard/soft gates, TDD, and NEXT_SKILL routing.

## Why This Change Was Made
Mermaid (GitHub-native) + Draw.io/SVG poster; multi-diagram pack for maintainability.

## User Impact
Any LLM/operator reads ship-flow-detailed.md; products get copy on install.

## Evidence pack
| Item | Result |
|------|--------|
| hard_gates | score |
| validate | full (repo) |
| smoke | product_smoke |
| remote | origin/main + tag v1.4.14 |

## Evidence
```text
TDD N/A (docs-only)
green_cmd: python3 scripts/product_smoke.py --root .
live: docs/ship-flow-detailed.md + diagrams on origin
```

## Red-proof
TDD N/A docs-only — Mermaid/SVG/docs only.

## Traceability
| AC | Evidence |
|----|----------|
| AC-1 detailed doc | docs/ship-flow-detailed.md |
| AC-2 Mermaid | embedded in detailed md |
| AC-3 Draw.io/SVG | docs/diagrams/ship-flow-overview.{drawio,svg} |
| AC-4 links + install | ship-flow, llm-bootstrap, skills-catalog, README, install_into_product.sh |

## Things that look bad but are actually fine
1. Version already tagged before formal FSM closeout this session
2. Diagram SVG is hand-authored companion to Draw.io
3. Product reinstall optional if already on 1.4.14 scripts

## Threat notes
- Asset: process truth for agents
- Abuse: ignoring hard_gates table — still enforced in hard_gates.py
