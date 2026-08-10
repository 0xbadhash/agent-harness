# HSQ-3 P2 — Spec hash, waiver budget, threat tags, security paths

**Version target:** 1.4.24  
**Date:** 2026-08-10

## Items

| ID | Gate |
|----|------|
| G2 | Spec file must exist; optional `spec_sha256:` in PR_DRAFT must match file |
| G10 | Waiver budget — fail if >N feature waivers (chore/hotfix) in 30d with large concurrent ship |
| G7 | Runtime threat notes must include ≥2 of fixed tags |
| G8 | `security_paths` in product_plugin — if diff hits them, require security test mention |

## AC

| ID | Criterion |
|----|-----------|
| AC-1 | Missing spec file fails G2 |
| AC-2 | Wrong spec_sha256 fails |
| AC-3 | Matching sha passes |
| AC-4 | Threat tags missing fails runtime |
| AC-5 | security_paths hit without test mention fails |
| AC-6 | security_paths miss → skip ok |
