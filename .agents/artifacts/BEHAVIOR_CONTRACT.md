# Behavior contract — top-50 gap closure

**Marker:** BEHAVIOR-CONTRACT
**Surface:** CLI tools and one scheduled workflow. No HTTP route, UI, or API.

| Clause | Observable |
|--------|------------|
| B1 | `check_glossary.py --root <repo>` prints the term count and exits 0; a duplicate normalized term prints a collision and exits 1. |
| B2 | `check_comment_audit.py --path <file> --classify` prints `kind → route` per finding; `--constraints` exits 1 on an unbounded constraint and 0 when a test name or waiver is present. |
| B3 | `check_ticket_dag.py <tickets>` treats `None — can start immediately` as no edge and prints the ready frontier. |
| B4 | `merge_stack.py --tickets <tickets> --dry-run` prints `would merge <id>` and exits 0. |
| B5 | `check_prototype_fidelity.py --spec <spec>` exits 1 when a named prototype has no `**Prototype use:** reference`, and 0 when it does. |
| B6 | `tools/weekly_retro.py --root <repo>` prints `no run records; nothing to retro` and exits 0 when `var/state` is absent. |
| B7 | `product_smoke.py --root .` reports 2/2 and `validate.py full` reports 9/9. |
