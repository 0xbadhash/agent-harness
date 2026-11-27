# Behavior contract — T2088U harness wiring

**Marker:** BEHAVIOR-CONTRACT
**Surface:** CLI scripts and generated artifacts. No web UI.

| # | Clause | Pass condition |
|---|--------|----------------|
| B1 | Ticket DAG | `check_ticket_dag.py` exits 0 and prints the ready frontier for a valid directory; exits 1 on a cycle. |
| B2 | Stack plan | `stack_plan.py --tickets <dir> --json` exits 0 and reports one layer per dependency generation. |
| B3 | Stack plan write | `--write` creates `.agents/artifacts/STACK_PLAN.md` and `.json`. |
| B4 | Unknown dependency | `stack_plan.py` exits 1 and names the missing ticket. |
| B5 | Retro issue bodies | `retro_job.py --file-issues` exits 0, writes one body per cluster plus an umbrella body. |
| B6 | Offline default | No subprocess/network call runs without `--gh`; `--gh` alone exits 2. |
| B7 | Spec gate | `spec_gate.py` exits 0 on the ship spec and rejects a colliding glossary. |
| B8 | Comment audit | `check_comment_audit.py --diff 0336317...HEAD --strict` exits 0. |
| B9 | Smoke | `product_smoke.py` exits 0 with both steps green. |
