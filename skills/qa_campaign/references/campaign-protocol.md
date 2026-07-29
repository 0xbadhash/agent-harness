# FULL END-TO-END AUTONOMOUS QA + BUG HUNT + ROOT-CAUSE FIX CAMPAIGN

Load this when `/qa_campaign` is running. Product adapts categories to its stack.

## Mission

Perform a complete, multi-layered quality assurance campaign on the **current repository**.

Goal: discover **at least 200 distinct, real bugs** when the codebase scale allows
(functional, correctness, performance, security, reliability, edge-case, concurrency,
resource-leak, etc.). On smaller repos: exhaust honestly — never invent filler bugs.

For every bug found:

- Diagnose the **root cause** (not symptoms).
- Implement a proper fix (refactor allowed if it improves design within boundaries).
- Never apply band-aids, workarounds, or temporary patches.
- After every fix, the system must remain behaviourally identical for all previously working paths (no regressions).

At the end the codebase must be **functionally equivalent** to the starting state except free of discovered bugs.

## Orchestration rules

- You are the **Orchestrator**. Spawn as many specialized sub-agents as needed.
- Use git worktrees liberally (one worktree per major investigation or fix branch).
- Spin up multiple independent development servers / gateways on different ports when required for parallel testing.
- Create clean, atomic pull requests for every logical group of fixes.
- Keep a live running tally of bugs found / fixed. Stop only when ≥ 200 unique bugs have been fixed **or** the codebase is exhausted.

## Mandatory test coverage (all types)

Systematically exercise every category below that applies. Mark N/A with reason when the product has no such surface.

1. **Unit tests** – pure functions, classes, modules (property-based / generative where useful).
2. **Integration tests** – service ↔ service, DB, external API, queues, caches.
3. **End-to-end / system tests** – full user journeys through the real running application (API + UI if present).
4. **Contract / consumer-driven tests** – API contracts, schema, protobuf/OpenAPI compatibility.
5. **Stress / load / soak tests** – high concurrency, high volume, long-running sessions.
6. **Performance / profiling tests** – latency, throughput, memory, CPU, GC, N+1, hot paths.
7. **Concurrency & race-condition tests** – simultaneous writes, transactions, locks, eventual consistency.
8. **Chaos / fault-injection tests** – partitions, process kills, disk full, latency, corrupted responses, clock skew.
9. **Security tests** – authz/authn bypass, injection, IDOR, SSRF, path traversal, secret leakage, rate-limit bypass (defensive only).
10. **Edge-case & boundary tests** – empty, max sizes, unicode, null bytes, negatives, timezone extremes, leap seconds.
11. **Regression tests** – for every fixed bug so it cannot reappear.
12. **Compatibility / migration tests** – schema migrations, data upgrades, config/API compatibility.
13. **Observability tests** – metrics, logs, traces, health checks surface problems correctly.
14. **Resource-leak & cleanup tests** – handles, connections, threads/goroutines, memory, temp files, listeners.

## Execution protocol

1. Create a clean baseline: full existing suite + start the application; record golden behaviour (API responses, DB state, metrics).
2. Partition the codebase into logical domains. Assign each domain to one or more specialist sub-agents.
3. For each domain:
   - Isolated worktrees + independent gateways on unique ports when needed.
   - Full matrix of test types.
   - Failure/anomaly → detailed investigation ticket (inventory row).
4. For every confirmed bug:
   - Minimal deterministic reproduction (test or script).
   - Root-cause analysis (stack, data flow, design).
   - Correct fix (refactor OK inside module boundaries).
   - Regression test that would have caught the bug.
   - Verify no golden behaviour change.
   - Commit with clear message; open PR (or push worktree branch).
5. Continuously merge green PRs; re-run full regression after every merge.
6. Living inventory of every bug (ID, category, root cause, fix commit, PR link).

## Reporting

When the campaign reaches ≥ 200 fixed bugs **or** the codebase is exhausted, produce a comprehensive **Test Report** and write it into the product vault when enabled, e.g.:

`QA/YYYY-MM-DD_Full-E2E-Bug-Hunt-Report.md`

Also keep `.agents/artifacts/QA_CAMPAIGN_REPORT.md` in-repo.

The report must contain:

- Executive summary (bugs found / fixed, severity distribution, time spent).
- Full inventory with root-cause analysis and fix references.
- Coverage matrix (which test types found which classes).
- Residual risks / areas not fully exercised.
- Recommendations for permanent test infrastructure.
- Exact commands / scripts so the campaign can be re-run.

## Hard constraints

- Never change external behaviour for any previously working scenario.
- Never leave the repository in a broken state.
- Prefer deep architectural fixes over local patches.
- Prefer adding missing tests over silencing existing ones.
- All PRs must be self-contained and reviewable.
- Do not advance ship pipeline phases; do not auto-tag/release from this skill.
