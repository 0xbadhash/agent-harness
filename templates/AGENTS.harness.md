# AGENTS.md — product + harness

Contract for any coding agent (any LLM) working in this repo.

## Product intent

<!-- Replace with your product one-liner -->
Describe what this product does and safe defaults.

## Agent harness (ship pipeline)

Portable skills installed under `.agents/skills/` from **agent-harness**.

```text
init
  → /spec                 # REQUIRED for features (or Spec waiver: hotfix|chore|docs-only)
  → /execute_dev          # implement (TDD); runs spec_gate
  → /code_review          # required closeout (non-prose)
  → /cross_review         # if NEXT_SKILL says so (large)
  → /behavior_validator   # if NEXT_SKILL says so (runtime)
  → /pr_review --validate # hard gates + score ≥ 95 → approved
  → /release_mgmt         # smoke + tag → shipped
  → /sync_docs            # docs stamps → init
  → /qa_campaign          # only if large ship (or --force-qa)
```

**Start a feature:** `.agents/docs/start-a-feature.md`  
`python3 scripts/start_feature.py --slug my-feature --write-spec-stub`

**Any LLM:** load `SKILL.md` from `.agents/skills/<name>/` when the user names `/name`.  
**Do not invent the next step** — run:

```bash
python3 scripts/next_skill.py --after <skill_just_finished>
```

and follow the printed `NEXT_SKILL=…` line.

Docs (installed): `.agents/docs/llm-bootstrap.md`, `.agents/docs/ship-flow.md`.

| Check | Command |
|-------|---------|
| Phase | `python3 scripts/pipeline_state.py get` |
| Skills | `python3 scripts/verify_skills.py` |
| Install health | `bash scripts/bootstrap_check.sh` |
| Smoke | `python3 scripts/product_smoke.py --root .` |
| Web E2E / Comet | `python3 scripts/check_web_e2e.py --root .` — **mandatory** when website/app detected |

**Website / browser-app products (fail closed):** every UI ship must update **Playwright** (`e2e/` with `Sxx` test titles) **and** **Comet scenarios** (every S-id must appear in the doc), keep `web_e2e.surfaces` + `smoke[]` e2e.  
Gate is hard in `/pr_review` and `/release_mgmt`. Opt out: `web_e2e.enabled: false`.  
Scaffold: `python3 scripts/scaffold_web_e2e.py --root . --write`.  
Guide: `docs/web-e2e-comet.md` (installed under `.agents/docs/` when present).

Pipeline state: `.agents/state/pipeline.json`  
Plugin: `.agents/product_plugin.yaml` (edit stack + smoke + optional `web_e2e` for *your* language)

## One-shot user phrase

```text
Full FSM for <task>: /execute_dev then /code_review then (if NEXT_SKILL says)
/cross_review and/or /behavior_validator then /pr_review --validate
then (if required) /vps_infra_ops --verify then /release_mgmt then /sync_docs
then git push origin main --tags then (optional) /qa_campaign
```

See `.agents/docs/ship-flow.md` and `.agents/docs/skills-catalog.md`.
