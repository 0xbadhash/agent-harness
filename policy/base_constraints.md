# Base Constraints (inherited by all `.agents/skills/*`)
## Product vs harness
- **Product** = watchlist app (`migration/`, `docs/PRODUCT.md`). **Harness** = this `.agents/` tree.
- Do not mix harness backlog into product `BACKEND_ROADMAP` Shaping. See `docs/PRODUCT_BOUNDARY.md`.

## Router & workflow (Principles 0–3)
- First action: read `AGENTS.md` (vault) + `GEMINI.md` (routing) + `.agents/README.md`. Session phases: `.agents/AGENT_WORKFLOW.md`.
- After significant **product** change: **run the app** (health.php / targeted tests) before handoff.
- Long tasks: prefer `.agents/traces/<task-id>.md` via `scripts/generate_worksheet.py`.

## Pipeline
- Flow: `docs/ARCHITECTURE.md` § Agentic Pipeline Flow
- State: `.agents/state/pipeline.json` via atomic CLI only

## Handoff Discipline
- Read only files declared in the skill's Reads line
- Write only files declared in the skill's Writes line
- Include §9 "Things that look bad but are actually fine" in reports

## §9 "Things that look bad but are actually fine" Schema
Every completion report MUST include this section with **minimum 3 entries** in YAML format:
```yaml
things_that_look_bad_but_are_fine:
  - file: "api/processing_api.[ext]:218"
    concern: "Dead code after unconditional raise"
    why_fine: "Legacy error path preserved for backward compatibility; tested in test_legacy_error_handling"
    validation: "[test_runner] tests/test_legacy_error_handling -v"
  - file: "config/settings.[ext]:92"
    concern: "Hardcoded localhost URL"
    why_fine: "Settings model default with ENV override; excluded from hardcode policy"
    validation: "[grep_equivalent] 'ENV_OVERRIDE' config/ tests/"
  - file: "tests/conftest.[ext]:45"
    concern: "Async backend fixture forces specific runtime"
    why_fine: "Prevents alternative runtime failures without adding dependency"
    validation: "[test_runner] tests/test_async_operations -v"
```
**Rules:**
- Each entry must cite `file:line`
- `concern` must describe what looks wrong
- `why_fine` must explain the intentional design decision
- `validation` must provide a command to verify the claim
- If audit finds <3 entries → shallow audit (policy failure)

## TDD Boundary (enforced by `/execute_dev` step 3)
- Red → Green → Refactor for every behavior/code change
- Red-phase tests assert through public contract (entry → validated output); new tests must fail before implementation lands
- At least one test exercises full path for cross-layer changes
- Schema-enforced outputs: no internal fields leak to final object
- Docs-only changes: explicit TDD N/A in handoff

## Anti-Patterns
- See `docs/AGENT_REFERENCE.md` for rebuttals
- Never skip validation gates
- Never subprocess validator from inside test runner

## Tooling
- Paths resolve via `utils/path_resolver` (or language equivalent)
- API/CLI-first; zero UI unless explicitly scoped
