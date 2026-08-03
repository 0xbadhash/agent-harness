# LLM bootstrap — any coding agent

How **any** LLM (Grok, Claude, Cursor, Codex, local models, …) discovers and runs the ship FSM after install.

## 1. Install (once per product)

```bash
# Pin a release for reproducibility
export AGENTS_HARNESS_ROOT=~/agent-harness   # clone of this repo
cd /path/to/your-product
"$AGENTS_HARNESS_ROOT/install_into_product.sh" . --verify
```

`--verify` runs `scripts/bootstrap_check.sh` (skills + scripts + pipeline present).

## 2. What the LLM must read

| Path | Why |
|------|-----|
| `AGENTS.md` | Product intent + ship pipeline summary |
| `.agents/product_plugin.yaml` | Stack, smoke commands, roadmap path |
| `.agents/skills/*/SKILL.md` | Slash skills (YAML `description` = load trigger) |
| `.agents/docs/ship-flow.md` | FSM phases and order |
| `.agents/docs/skills-catalog.md` | When each skill fires |
| `.agents/state/pipeline.json` | Current phase (do not invent phases) |

Agents that auto-load skills from `.agents/skills/` (or a configured skills path) only need a user message that names the slash skill.

## 3. Full FSM — one user message

```text
Full ship FSM for <task description>:
/execute_dev then /code_review then (if NEXT_SKILL says) /cross_review
and/or /behavior_validator then /pr_review --validate
then (if required) /vps_infra_ops --verify then /release_mgmt
then /sync_docs then git push origin main --tags
then (optional, large releases) /qa_campaign
```

Shorter:

```text
Ship <task> end-to-end: execute → code-review → pr-review --validate → release → sync-docs → push
```

**Front door (required for features):**

```text
/spec <idea> then full FSM
```

Or scaffold files then implement:

```bash
python3 scripts/start_feature.py --slug my-feature --write-spec-stub
# then /execute_dev after refining acceptance
```

Hotfix / docs without a full spec interview:

```text
**Spec waiver:** hotfix   # or chore | docs-only | prose-only
```

Guide: [start-a-feature.md](start-a-feature.md) (installed as `.agents/docs/start-a-feature.md`).

Always run and obey:

```bash
python3 scripts/next_skill.py --after <just-finished-skill>
# exactly one line: NEXT_SKILL=/…
```

Map: [ship-flow.md](ship-flow.md) · catalog: [skills-catalog.md](skills-catalog.md)

## 4. Phase gates (agent must respect)

**Full FSM (states + transitions + skill branches):** [ship-flow.md](ship-flow.md)  
**Detailed (skills · hard/soft gates · TDD · Mermaid + poster):** [ship-flow-detailed.md](ship-flow-detailed.md)  
(product install: `.agents/docs/ship-flow.md` · optional detailed copy when installed)

```text
init → ready_for_review → approved → shipped → init
                 └─► blocked ──(fix /execute_dev)──► ready_for_review
```

| Skill | Needs phase | Sets phase |
|-------|-------------|------------|
| `/spec` | any | *(none)* |
| `/execute_dev` | `init` or `blocked` | `ready_for_review` |
| `/code_review` / `/cross_review` / `/behavior_validator` | (after implement) | *(none)* — print `NEXT_SKILL=` only |
| `/pr_review --validate` | `ready_for_review` | `approved` or `blocked` |
| `/vps_infra_ops --verify` | `approved` | *(none)* — **only if required** for product; then `NEXT_SKILL=/release_mgmt` |
| `/release_mgmt` | `approved` | `shipped` |
| `/sync_docs` | `shipped` | `init` |
| `/qa_campaign` | any (after full FSM) | *(none)* — deep QA; suggested after `/sync_docs` |

Check:

```bash
python3 scripts/pipeline_state.py get
```

## 5. Next-step router (do not invent the next skill)

After each step the agent should run:

```bash
python3 scripts/next_skill.py --after execute_dev --base HEAD~1 --head HEAD
python3 scripts/next_skill.py --after code_review
python3 scripts/next_skill.py --after behavior_validator
# prints exactly one line: NEXT_SKILL=/pr_review --validate
```

## 6. Ship-chain skills (must install)

From `config/ship_skills.txt` / `.agents/policy/ship_skills.txt`:

Ship-chain: `spec` · `execute_dev` · `code_review` · `cross_review` · `behavior_validator` · `pr_review` · `release_mgmt` · `sync_docs` · `qa_campaign`  

Support (also installed): `plan_backend` · `audit_repo` · `audit_harness` · `sweep` · `feedback` · `test_automation` · `night_shift` · `handoff` · `session_viewer` · `agent_transcript`  

Product-only (not in portable harness): `vps_infra_ops` when the product needs infra verify.

Verify:

```bash
python3 scripts/verify_skills.py
bash scripts/bootstrap_check.sh
```

## 7. Product plugin (stack is yours)

Harness is **language-agnostic**. Set smoke to *your* test command:

```yaml
smoke:
  - name: unit
    # Prefer a wrapper script over bash -c (YAML quote breakage under night_shift)
    cmd: ["bash", "scripts/smoke_unit.sh"]   # or: npm test, go test, cargo test, …
```

## 8. Failure modes for LLMs

| Symptom | Fix |
|---------|-----|
| `WRONG STATE` | Run `pipeline_state.py get`; only run skill allowed in that phase |
| Skills not found | Re-run `install_into_product.sh . --verify` |
| Agent skips review | Require `NEXT_SKILL=` line; do not jump to release |
| Empty smoke | Edit `product_plugin.yaml` smoke[] |

## Related

- [bootstrap.md](bootstrap.md) — clone → install → first task  
- [ship-flow.md](ship-flow.md) — FSM detail  
- [skills-catalog.md](skills-catalog.md) — all skills  
