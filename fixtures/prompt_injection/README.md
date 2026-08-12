# Prompt-injection fixtures (Tier B-4)

Synthetic attack strings for **offline** unit tests of product filters / harness review scope.
Do **not** send these to production LLM endpoints in CI without isolation.

| File | Intent |
|------|--------|
| `ignore_instructions.txt` | Classic "ignore previous instructions" |
| `tool_exfil.txt` | Attempt to exfiltrate tools/env |
| `role_hijack.txt` | Force system-role rewrite |

Run harness self-check: `python3 scripts/check_pi_fixtures.py`
