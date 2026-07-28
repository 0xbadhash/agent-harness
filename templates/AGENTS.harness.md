# AGENTS.md — product + harness

Contract for any coding agent (any LLM) working in this repo.

## Product intent

<!-- Replace with your product one-liner -->
Describe what this product does and safe defaults.

## Agent harness (ship pipeline)

Portable skills installed under `.agents/skills/` from **agent-harness**.

```text
init
  → /spec (optional)      # acceptance + roadmap OPEN
  → /execute_dev          # implement (TDD when code)
  → /code_review          # structure closeout (non-prose)
  → /cross_review         # if NEXT_SKILL says so (large/security)
  → /behavior_validator   # if NEXT_SKILL says so (runtime surface)
  → /pr_review --validate # score ≥ 95 → approved
  → /release_mgmt         # smoke + tag → shipped
  → /sync_docs            # docs stamps → init
```

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

Pipeline state: `.agents/state/pipeline.json`  
Plugin: `.agents/product_plugin.yaml` (edit stack + smoke for *your* language)

## One-shot user phrase

```text
Full FSM for <task>: /execute_dev then /code_review then (if NEXT_SKILL says)
/cross_review and/or /behavior_validator then /pr_review --validate
then (if required) /vps_infra_ops --verify then /release_mgmt then /sync_docs
then git push origin main --tags
```

See `.agents/docs/ship-flow.md` and `.agents/docs/skills-catalog.md`.
