# Agent Reference: Anti-Rationalizations
| Rationalization | Rebuttal | Exit Criteria |
|---|---|---|
| "CI will catch it later" | Shift-left mandatory | [type_checker]/[linter]/[test_runner] pass on diff |
| "Only tests fail, production is fine" | Still blocks if new tests fail | [test_runner] exits 0 |
| "[Type_checker] errors are pre-existing" | Verify with diff-first | Clean on changed files |
| "I'll fix next task in same PR" | Single-step only | One roadmap item per cycle |
| "UI makes this easier" | Prefer API/CLI when equal; **product desk UI is allowed** when the task is watchlist UX | Scope in task AC; no SPA/CDN |
| "Skip cross_review" | Soft-gate warns on large diffs | `/cross_review` then evidence in PR_DRAFT |
| "Small hardcode is fine" | Blocks compliance | Hardcode scan passes |
| "Phase is shipped so skip gate" | Enforce FSM | pipeline.json matches gate |
| "Coverage is high globally" | Module thresholds apply | Per-module check passes |
| "Mock paths are harmless" | Fails hygiene check | No generic mocks at root |
| "Spec is implied" | Missing criteria = halt | Task has acceptance criteria |
| "I'll add tests after" | TDD red-green required | Tests exist + pass after impl |
| "Helper tests cover refactor" | Test public boundary | Entry → validated output |

## Phase Gate Reference
| Skill | Required Phase | Writes Phase |
|---|---|---|
| execute_dev | init/blocked/missing | ready_for_review |
| cross_review | any (prefer **before** pr_review on large diffs) | none (artifact / PR_DRAFT section) |
| pr_review | ready_for_review | approved/blocked (+ soft cross_review warn) |
| vps_infra_ops --verify | approved/shipped | (none; writes `.agents/artifacts/INFRA_RUNBOOK.md`) |
| release_mgmt | approved (≥95) + infra verify PASS | shipped |
| sync_docs | shipped | init (+ vault dev-log via `scripts/sync_vault_devlog.py`) |
| feedback | any | none (writes `.agents/AGENT_FEEDBACK.md`) |
| sweep | any | none (hygiene report) |

Session phases (non-FSM): `.agents/AGENT_WORKFLOW.md`. Harness home: `.agents/README.md`. Product: `docs/PRODUCT.md`. Principle index: `GEMINI.md`.
