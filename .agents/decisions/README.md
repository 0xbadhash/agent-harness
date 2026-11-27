# Architecture decision records

One file per decision, named `NNN-<slug>.md`, numbered in order. The status is
`proposed`, `accepted`, `superseded`, or `rejected`. A superseded record names
its replacement.

`scripts/check_adr.py` validates this index: every ADR file appears here, every
link here resolves, and every accepted ADR states reversibility, surprise, and
tradeoff. `/spec` reads the relevant records before grilling.

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-review-tiers-by-door.md) | Tier review depth by door class | accepted |
