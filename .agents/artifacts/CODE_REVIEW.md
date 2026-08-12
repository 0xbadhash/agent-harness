# CODE-REVIEW
**Marker:** CODE-REVIEW
**Scope:** CI matrix steps 1–5 + docs/ci-matrix.md (v1.4.26)

## Findings
- Product daytime template is fail-closed when harness scripts exist.
- Skip hard gates gated by ALLOW_SKIP_HARD_GATES=1 (J6).
- Semgrep config high-signal only; ZAP warn-only for staging hosts.
- property_tests opt-in via product_plugin (no false fails).
- install_into_product refreshes daytime-gates.yml on force install.

## Verdict
Approve for merge after unit tests and pr_validator green.
