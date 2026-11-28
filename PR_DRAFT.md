# PR Draft: Default /challenge to local agy CLI backend

**Range:** `origin/main...HEAD`

**Spec waiver:** chore
**Plan:** `.agents/specs/2026-11-27-outstanding-ops-plan.md`

## What Problem This Solves

`/challenge` previously routed exclusively through external GLM and Venice/DeepSeek APIs instead of using the local Antigravity CLI (`agy`) authed as `jeanclaude.mansart@gmail.com`.

## Why This Change Was Made

Adds `call_agy(prompt, model)` to `scripts/challenge.py` as the default `--backend agy` path (`gemini-4-carbon-high` round 1, `gemini-4-hydrogen-high` round 2), while keeping GLM/DeepSeek intact behind an explicit `--backend api` fallback flag. Updates `skills/challenge/SKILL.md` and adds a fixture-driven test in `tests/test_challenge.py`.

## User Impact

- `/challenge` defaults to local `agy -p` (`jeanclaude.mansart@gmail.com`).
- Existing `--backend api` (GLM/DeepSeek) remains available via explicit flag.

## Evidence

- `python3 -m pytest -q tests/test_challenge.py tests/test_skill_drift.py` (`16 passed`)
- `python3 scripts/validate.py full`
- `python3 scripts/check_secrets_diff.py --base origin/main --head HEAD`

## Merge Danger

**Door:** two-way
**Blast Radius:** Low. Scoped to `scripts/challenge.py`, `skills/challenge/SKILL.md`, `tests/test_challenge.py`, and `tests/fixtures/challenge_agy_recorded.json`.

## Threat notes

**Tags:** secrets, injection

- **Assets:** local `agy` CLI invocation, proposal/decision markdown, vault challenge notes.
- **Abuse cases:** shell injection via prompt text or credential leakage in logs. `call_agy` uses list-argv `subprocess.run` (`shell=False`) with `--disable-slash-commands`, and never reads or prints OAuth tokens.
- **Boundaries:** No network listeners; explicit `--backend api` opt-in for external APIs.

## Traceability

| AC | Test / command |
|----|----------------|
| AC-agy default | `tests/test_challenge.py::ChallengeAgyBackendTests::test_agy_default_backend_uses_recorded_fixture` |
| AC-agy missing bin | `tests/test_challenge.py::ChallengeAgyBackendTests::test_call_agy_missing_binary_raises_model_error` |
| AC-api fallback | `tests/test_challenge.py::ChallengeTests` |
| AC-skill drift | `tests/test_skill_drift.py` |

## Red-proof

```text
red_cmd: git show origin/main:scripts/challenge.py | python3 -c "import sys; sys.exit(0 if 'call_agy' in sys.stdin.read() else 1)"
green_cmd: python3 -m pytest -q tests/test_challenge.py
```

Red exits 1 on `origin/main` (before `call_agy` existed). Green runs `tests/test_challenge.py`.

## Evidence pack

- `hard_gates`: `python3 scripts/hard_gates.py --diff origin/main...HEAD`
- `pytest`: `16 passed` on `tests/test_challenge.py tests/test_skill_drift.py`
- `validate`: `python3 scripts/validate.py full`

## Things that look bad but are actually fine

1. `call_glm` and `call_deepseek` remain in `scripts/challenge.py` behind `--backend api` as required fallback.
2. `skills/challenge/SKILL.md` retains `z-ai-glm-5-3-flash`, `ask_glm.py`, `deepseek-v4-flash`, and `Venice` in the `--backend api` section (also checked by `tests/test_skill_drift.py`).
3. `AGY_ACCOUNT` is a non-secret email identifier (`jeanclaude.mansart@gmail.com`) recorded in challenge metadata.
