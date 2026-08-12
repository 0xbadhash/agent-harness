# Spec: Tier A/B/C Best-of-Agent-Harnesses features (1.4.28)

**Status:** implement  
**Product:** agent-harness  
**Version:** 1.4.28

## Goal

Ship portfolio-ready Tier A (must), Tier B (should), and Tier C (scaffold) capabilities recommended after Best-of-Agent-Harnesses assessment — without building multi-agent runtime (NON_GOAL).

## Acceptance criteria

| ID | Criterion | Test / evidence |
|----|-----------|-----------------|
| AC-1 | `harness.manifest.yaml` validates classification + capabilities | `check_harness_manifest.py` + unit |
| AC-2 | Compatibility claimed vs tested matrix + doc alignment | `docs/compatibility.md` + `check_compatibility.py` |
| AC-3 | Critical SoT scripts list + report/merge tool | `protect_sot_merge.py` + `config/critical_sot_scripts.txt` |
| AC-4 | `SCANNER_STRICT` forces fail when scanners missing | secrets + lockfile audit + unit |
| AC-5 | MCP contract doc + optional product_plugin check | `check_mcp_contract.py` |
| AC-6 | Recovery demo proves resumable pipeline re-read | `recovery_demo.py` |
| AC-7 | Evidence content hashes for ship artifacts | `evidence_hash.py` |
| AC-8 | Prompt-injection fixtures offline | `fixtures/prompt_injection/*` + `check_pi_fixtures.py` |
| AC-9 | GitHub daytime status for OPS | `github_daytime_status.py` + ops_dashboard embed |
| AC-10 | Tier C scaffolds + C15 NON_GOAL | benchmark, sbom/signing, sandbox doc, telemetry, manifest non_goals |

## Non-goals

- Multi-agent runtime / owning inference loop
- Fail-closed SBOM for all products in this release
- Applying protect_sot_merge --apply to every product (report-only default)

## Risks

- GitHub API rate limits on OPS dashboard refresh → best-effort embed
- SCANNER_STRICT breaks offline sandboxes if set globally without tools

## Traceability

See PR_DRAFT Traceability table.
