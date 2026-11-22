# CONTEXT_PACK

**Generated:** 2026-11-08T10:07:49Z
**Root:** `/home/debian/agent-harness`

## Constitution / constraints

### .agents/policy/base_constraints.md

```
# Base Constraints (inherited by all skills)

## Product vs harness
- **Product** = application code + roadmap + domain (see `.agents/product_plugin.yaml`).
- **Harness** = skills, scripts, policy, pipeline FSM (this package / product `.agents/` install).
- Do not mix harness backlog into the product roadmap. Stack is chosen only in the product plugin.

## Router & workflow
- First action: product session policy (if any) + harness policy + skill for the task.
- After significant product change: run **smoke** from `product_plugin.yaml` (and targeted tests).
- Long tasks: optional worksheets under `.agents/traces/`.

## Pipeline
- State: `.agents/state/pipeline.json` via `scripts/pipeline_state.py` only (atomic).
- Flow: init → ready_for_review → approved → shipped → init (see docs/ship-flow.md).

## Handoff Discipline
- Read only files declared in the skill's Reads line
- Write only files declared in the skill's Writes line
- Include §9 "Things that look bad but are actually fine" in reports

## §9 Schema
Every completion report MUST include this section with **minimum 3 entries**:
```yaml
things_that_look_bad_but_are_fine:
  - file: "path:line"
    concern: "what looks wrong"
    why_fine: "intentional reason"
    validation: "command to verify"
```

## TDD Boundary (enforced by `/execute_dev` step 3)
- Red → Green → Refactor for every behavior/code change
- New tests must fail before implementation lands
- Docs-only: explicit TDD N/A in handoff
- PR_DRAFT narrative (see `templates/PR_DRAFT.md`): **What Problem This Solves**, **Why This Change Was Made**, **User Impact**, **Evidence**
- Optional **Red-proof** in PR_DRAFT: command that failed before green

## Anti-Patterns
- Never skip validation gates
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
  extra_dirs: []
  dev_log_rel: 01-Projects/agent-harness/dev-log.md
  mirror_docs: []

product_path_prefixes:
  - scripts/
  - bin/
  - skills/

domain_review_hints:
  - portable harness (no host-only defaults)
  - no secret leakage

# Harness SoT is not a web3/client_secrets product — traits stay off (auto).
traits:
  web: false
  web3: false
  client_secrets: false


night_shift:
  default_host: ""
  live_path: ""
  live_urls: []
  live_expect_code: "200"
  coverage_soft: "1"

product_skills: []
```
