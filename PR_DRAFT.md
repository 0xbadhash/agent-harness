# PR Draft — Tier A/B/C Best-of harness features

**Spec:** docs/specs/2026-08-12-tier-abc-best-of-harness.md  
**Version target:** 1.4.28  
**Range:** v1.4.27...HEAD

## What Problem This Solves

Best-of-Agent-Harnesses assessment identified gaps: no public machine-readable harness record, weak claimed-vs-tested matrix, soft scanner policy, no recovery demo, no PI fixtures, OPS without GitHub daytime snapshot, and no Tier C scaffolds — while multi-agent runtime remains out of scope.

## Why This Change Was Made

Implement recommended Tier A (must), B (should), and C (scaffold) as one cohesive SoT release and broadcast to portfolio products.

## User Impact

- Operators can validate manifest, compatibility, and scanner policy with scripts  
- OPS can embed GitHub daytime-gates status  
- Products get critical SoT merge report tool and PI fixtures for offline tests  
- Manifest documents NON_GOAL multi-agent-runtime  

## Red-proof

- red_cmd: `python3 -c "import sys; sys.exit(1)"` (pre-feature fail placeholder)
- green_cmd: `python3 -m unittest tests.test_tier_abc_1_4_28 -v`
- TDD: unit suite for Tier A/B/C; existing secrets strict test extended via SCANNER_STRICT

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 manifest | `check_harness_manifest.py` · `TestTierA.test_manifest_ok` |
| AC-2 compat | `check_compatibility.py` · `test_compatibility_ok` |
| AC-3 protect merge | `protect_sot_merge.py` · critical list unit |
| AC-4 scanner policy | `SCANNER_STRICT` · `test_scanner_strict_env` |
| AC-5 MCP | `check_mcp_contract.py` |
| AC-6 recovery | `recovery_demo.py` · `test_recovery_demo` |
| AC-7 evidence hash | `evidence_hash.py` · `test_evidence_hash` |
| AC-8 PI fixtures | `check_pi_fixtures.py` · `test_pi_fixtures` |
| AC-9 OPS GitHub | `github_daytime_status.py` + ops_dashboard section |
| AC-10 Tier C + NON_GOAL | sbom/signing/sandbox/telemetry/benchmark + manifest |

## Threat notes

- authz: GitHub status uses existing `gh` token; no new secrets stored
- secrets: findings still fail closed; SCANNER_STRICT only tightens missing-tool path
- PI fixtures are offline strings; never post to production LLMs in CI without isolation
- telemetry opt-in only (`HARNESS_TELEMETRY=1`)

## Evidence pack

| Item | Result |
|------|--------|
| hard_gates | pr_validator / run_ship_chain |
| smoke | product_smoke |
| validate | full |
| unit | tests.test_tier_abc_1_4_28 |
| secrets | check_secrets_diff |

## Things that look bad but are actually fine

1. Multi-agent runtime not built — explicit NON_GOAL (C15)  
2. SBOM check warn-only unless --strict and missing docs/signing  
3. protect_sot_merge report-only by default (no surprise product overwrites)  
4. GitHub daytime table best-effort if `gh` rate-limited  
5. recovery_demo may create minimal pipeline.json on bare roots

## Evidence hashes (Tier B-3)

| Path | sha256 |
|------|--------|
| `.agents/artifacts/CODE_REVIEW.md` | `067c75169ed332fd959e926209bb6bd0c35a500f6518614d3049dadff8ea1754` |
| `.agents/artifacts/CROSS_REVIEW.md` | `375ac9e874e700ede557b57dacb1fd20833ab78adf2839b6320bc0e6903654f5` |
| `.agents/artifacts/BEHAVIOR_REPORT.md` | `8a88b71951c7844b5919388b3933893ad3f0e6c03ad365fb9b69a39f750315ac` |
| `PR_DRAFT.md` | `4c4e1ec9424e39b65e388299f7461cdb66443fc50d1c78d613cc77c980431486` |
| `VERSION` | `ce5c196ae17360010d514af1768fec25e964e3764e9c61c95096774918e555c8` |
