# CODE-REVIEW

**Marker:** CODE-REVIEW  
**When:** 2026-08-10  
**Scope:** HSQ-3 P0 — G1 AC map, G5 secrets, G14 diff compile

## Findings

- AC map fails closed only when Spec lists AC-n; waivers skip (correct).
- Path confinement on spec path under product root.
- Secrets patterns high-signal; JWT/sk-/npm_/AIza/stripe/bearer added.
- py_compile uses temp cfile — no .pyc pollution.
- hard_gates wiring matches secrets placement; prose-only skips G1/G14.

## Verdict

Approve P0 for merge after unit tests green.
