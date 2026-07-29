---
name: qa_campaign
description: >
  Full end-to-end autonomous QA + bug-hunt + root-cause fix campaign after a large
  release or full ship FSM. Orchestrate subagents, worktrees, multi-layer tests
  (unit→chaos→security), fix root causes only, write vault QA report. Trigger:
  /qa_campaign, post-sync_docs NEXT_SKILL, huge codebase release, deep bug hunt.
  Does NOT advance pipeline phase. Skip for tiny docs-only ships.
disable-model-invocation: true
user-invocable: true
max-retries: 0
timeout-seconds: 0
preserve-artifacts-on-failure: true
---

# Anti-patterns: policy/AGENT_REFERENCE.md · base_constraints
# `/qa_campaign` — full E2E autonomous QA + bug hunt + root-cause fix

**Not** a ship FSM phase. Run **after** a complete ship cycle (especially large
releases) or when the user invokes `/qa_campaign` explicitly.

Suggested automatically after `/sync_docs` via:

```bash
python3 scripts/next_skill.py --after sync_docs
# → NEXT_SKILL=/qa_campaign
```

Skip with `python3 scripts/next_skill.py --after sync_docs --skip-qa` or user says skip.

Deep protocol: [references/campaign-protocol.md](references/campaign-protocol.md).

---

## When

- User runs `/qa_campaign` or pastes a full E2E QA campaign brief
- **After full FSM** (`/sync_docs` completed → `NEXT_SKILL=/qa_campaign`)
- Huge release / multi-module refactor / high blast-radius change
- User asks for deep bug hunt, stress, chaos, security sweep on **this** repo

**Skip / do not load:** tiny prose-only ships, mid-ship remediation, when user
opts out. Prefer `/night_shift` for routine overnight readiness only.

## Mission

Perform a complete, multi-layered quality assurance campaign on the **current
repository** (product root or harness SoT).

| Goal | Rule |
|------|------|
| Discover **many real bugs** | Functional, correctness, performance, security, reliability, edge, concurrency, resource-leak, etc. Target **≥200 distinct** when the codebase can sustain that depth; if smaller, **exhaust** the tree and report honest inventory (do not invent filler bugs). |
| Every bug | **Root cause** (not symptom) → proper fix → **regression test** |
| No band-aids | No workarounds, temporary patches, or silencing tests |
| No regressions | Behaviourally identical for previously working paths |
| End state | Functionally equivalent to start **except** free of discovered bugs |

## Orchestration (you are the Orchestrator)

1. Spawn specialized **sub-agents** as needed (domains, test types).
2. Use **git worktrees** liberally (one per major investigation or fix branch).
3. Spin independent dev servers / gateways on **different ports** for parallel testing when the product has runtime surfaces.
4. Create **atomic PRs** per logical fix group (or worktree branches ready for PR).
5. Keep a **live tally** of bugs found / fixed.
6. Stop when ≥200 unique bugs fixed **or** the codebase is exhausted (document which).

## Mandatory test matrix (do not skip categories)

Systematically exercise every category that applies to this repo’s stack
(`product_plugin.yaml`). Mark `out_of_scope` only when the product has no such
surface (e.g. no HTTP API → no HTTP chaos).

1. Unit (incl. property-based where useful)
2. Integration (service/DB/API/queue/cache)
3. E2E / system (real running app)
4. Contract / consumer-driven (OpenAPI/protobuf/schema)
5. Stress / load / soak
6. Performance / profiling
7. Concurrency & races
8. Chaos / fault injection
9. Security (authz, injection, IDOR, SSRF, secrets, rate limits)
10. Edge / boundary (empty, max, unicode, null, timezones, …)
11. Regression (auto-add tests for every fix)
12. Compatibility / migration
13. Observability (metrics, logs, traces, health)
14. Resource-leak & cleanup

## Execution protocol

1. **Baseline:** full existing suite + start app; record golden behaviour.
2. **Partition** codebase into domains; assign sub-agents.
3. Per domain: worktrees + isolated gateways; run full matrix; ticket anomalies.
4. Per confirmed bug:
   - Minimal deterministic reproduction
   - Root-cause analysis
   - Correct fix (refactor OK within module boundaries)
   - Regression test
   - Verify no golden-path change
   - Commit + PR / branch
5. Merge green PRs; re-run full regression after merges.
6. Living inventory: ID, category, root cause, fix commit, PR link.

## Artifacts (this repo)

| Path | Content |
|------|---------|
| `.agents/artifacts/QA_CAMPAIGN_INVENTORY.md` | Live tally + bug table (marker `QA-CAMPAIGN-INVENTORY`) |
| `.agents/artifacts/QA_CAMPAIGN_REPORT.md` | Final report (marker `QA-CAMPAIGN-REPORT`) |
| Product vault (if enabled) | `01-Projects/<label>/docs/` or  
  `QA/YYYY-MM-DD_Full-E2E-Bug-Hunt-Report.md` under vault root when `PRODUCT_VAULT_ROOT` set |

Use harness vault writers when available:

```bash
# Optional vault note (if vault enabled)
python3 scripts/sync_vault_devlog.py --note "QA campaign <date>" --bullet "…"
```

## Hard constraints

- Never change external behaviour for previously working scenarios.
- Never leave the repository broken.
- Prefer architectural fixes over local patches.
- Prefer adding missing tests over silencing existing ones.
- All PRs self-contained and reviewable.
- **Do not** set `pipeline.json` (phase stays whatever post-`/sync_docs` left, usually `init`).
- **Do not** auto-release or force-push.
- Never write exploits/malware PoCs for production attack; security tests stay defensive.

## Start sequence

1. Survey repo structure, existing tests, how the app starts (`product_plugin.yaml` smoke/stack).
2. Write inventory header + baseline results under `.agents/artifacts/`.
3. Spawn first wave of sub-agents; begin the hunt.
4. When done: final report + vault path if any.

## Handoff

```bash
python3 scripts/next_skill.py --after qa_campaign
# → NEXT_SKILL=(done)
```

Print:

```text
✅ QA-CAMPAIGN DONE  found=N  fixed=M  residual=K
NEXT_SKILL=(done)
```
