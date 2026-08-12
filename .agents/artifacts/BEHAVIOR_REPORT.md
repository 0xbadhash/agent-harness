# BEHAVIOR-REPORT — Tier A/B/C 1.4.28

**Marker:** BEHAVIOR-REPORT  
**Verdict:** PASS

## Scenarios

| # | Scenario | Result |
|---|----------|--------|
| 1 | check_harness_manifest on SoT | exit 0 |
| 2 | check_compatibility alignment | exit 0 |
| 3 | SCANNER_STRICT without gitleaks/trufflehog | exit 1 |
| 4 | recovery_demo creates/reads phase | exit 0 |
| 5 | check_pi_fixtures | exit 0 |
| 6 | check_sbom_signing (docs/signing.md) | exit 0 |
| 7 | telemetry default off | no file |
| 8 | unittest suite | 13 ok |

## Runtime surface

New scripts are CLI-only; no HTTP service. Behavior validated via unit + direct CLI runs.
