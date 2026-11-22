---
name: e2e_gate
description: >
  Run one product's existing Playwright scenarios and write a PASS/FAIL gate.
  On failure, one local fix loop only. Does not release.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 900
preserve-artifacts-on-failure: true
---

# `/e2e_gate` — Playwright scenario gate

One product. Existing scenarios only. Do not invent specs. Do not start `/release_mgmt`.

## Run

```bash
python3 scripts/e2e_gate.py --root <product>
```

The script reads `tests/e2e/**/*.spec.ts`, `tests/e2e/**/*.spec.js`, `e2e/**/*.spec.ts`, `e2e/**/*.spec.js`, and `tests/e2e/**/*_test.py`. It refuses Chromium `156.0.8078.4` (exit 2) before any scenario. It writes `.agents/artifacts/E2E_GATE.md` with marker `E2E-GATE` and `status: PASS` or `status: FAIL`.

Exit 0 is pass. Exit 1 is a failed or missing suite. Exit 2 is the refused build.

## Models

Grok Build is the only model that edits. On failure, Venice `z-ai-glm-5-3-flash` reviews once, oneshot, tools off, and sees only the failing assertion plus the patch. Do not send the run to Deepseek or OpenRouter.

## On FAIL

1. Grok Build fixes the smallest cause and adds a regression test (red, then green).
2. GLM flash reviews that diff once.
3. Re-run `scripts/e2e_gate.py` for the same product.
4. Stop after two rounds. Leave the gate FAIL if it is still red.

Do not call `/pr_review`, `/release_mgmt`, or `/sync_docs` from this skill.

## Handoff

```text
E2E-GATE status=PASS|FAIL exit=N
```
