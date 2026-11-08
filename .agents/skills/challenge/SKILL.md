---
name: challenge
description: >
  Send a proposal to GLM 5.3 flash and Deepseek, have each attack the
  other's critique, then file one local decision. Does not edit the repo
  or replace the ship reviews.
disable-model-invocation: true
user-invocable: true
metadata:
  hermes:
    tags: [challenge, review, glm, deepseek]
    related_skills: []
---

# /challenge

Use when the operator says `/challenge` and pastes or points at a proposal.

## Do

1. Save the proposal to a file. Do not attach the repo, the vault, or any `.env`.
2. From the product root, run:

```bash
python3 scripts/challenge.py --proposal path/to/proposal.md --vault /opt/second-brain/vault
```

Hermes, or any checkout without the installed script, runs the harness copy:

```bash
python3 ~/agent-harness/scripts/challenge.py --proposal path/to/proposal.md --root <product-root> --vault /opt/second-brain/vault
```

3. Exit 2 means both critiques are in `.agents/artifacts/CHALLENGE.md`. Read them. Write the decision yourself: what stayed, what changed, and which critique was rejected. Do not call a third model. Do not treat either model as the winner by default.
4. File it:

```bash
python3 scripts/challenge.py --proposal path/to/proposal.md --decision path/to/decision.md --vault /opt/second-brain/vault
```

Exit 0 writes the same note to `01-Projects/<project_label>/challenges/YYYY-MM-DD-<slug>.md` and a one-line pointer in that project's `decisions.md`.

## Vault must be named up front

`challenge.py` deliberately refuses instead of guessing a host vault — that safety rule is covered by
`tests/test_challenge.py::test_unset_vault_refuses_instead_of_host_default`. But it only checks the vault
at filing time, **after** both model rounds are paid for. Always pass `--vault` (or export
`PRODUCT_VAULT_ROOT`) in the *first* invocation, not just the `--decision` one, or the critiques are
written to `.agents/artifacts/CHALLENGE.md` and the vault note is lost.

## Do not

- Apply a patch from the decision.
- Replace `/code_review`, `/cross_review`, or `/pr_review`.
- Invent a missing model's side. Exit 1 means stop. The vault stays unchanged.
- If the vault write fails after both critiques, the decision is still printed and the exit code is 1. Say that. Do not claim it was logged.

## Models

GLM is `z-ai-glm-5-3-flash` through `/home/debian/hermes/scripts/ask_glm.py`. Deepseek is `deepseek-chat`. Keys stay in the Hermes env and are never printed.
