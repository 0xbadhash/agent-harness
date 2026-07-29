# CONTEXT_PACK

**Generated:** 2026-07-29T08:20:28Z
**Root:** `/home/debian/agent-harness`

## Constitution / constraints

### AGENTS.md

```
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
```

## Open risks / decisions

- (fill during /execute_dev)

## Plugin smoke

```yaml
product_id: agent-harness
product_name: Agent Harness
repo_root: .

stack:
  languages: [python]
  package_manager: pip
  test_runners: [pytest]
  app_layout: scripts/, bin/, skills/

product_roadmap: CHANGELOG.md
harness_backlog: .agents/BACKLOG.md

smoke:
  - name: hardcodes
    cmd: ["python3", "scripts/check_hardcodes.py"]
    cwd: .
  # Wrapper avoids nested bash -c / YAML quote breakage under night_shift
  - name: unit
    cmd: ["bash", "scripts/smoke_unit.sh"]
    cwd: .

vault:
  enabled: true
  root_env: PRODUCT_VAULT_ROOT
  default_root: ""
  project_label: agent-harness
  dev_log_rel: 01-Projects/agent-harness/dev-log.md
  mirror_docs: []

product_path_prefixes:
  - scripts/
  - bin/
  - skills/

domain_review_hints:
  - portable harness (no host-only defaults)
  - no secret leakage

night_shift:
  default_host: ""
  live_path: ""
  live_urls: []
  live_expect_code: "200"
  coverage_soft: "1"

product_skills: []
```
