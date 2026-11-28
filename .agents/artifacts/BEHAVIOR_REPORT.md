# BEHAVIOR-REPORT

- **Target:** `scripts/challenge.py` CLI and `product_smoke.py` (source-blind)
- **Date:** 2026-11-28

| Clause | Check | Result |
|--------|-------|--------|
| CLI help & default backend | `python3 scripts/challenge.py --help` | `pass` (exits 0; documents `--backend {agy,api}` with default `agy`) |
| Empty proposal guard | `printf '' \| python3 scripts/challenge.py --proposal -` | `pass` (exits 1 with `empty proposal`, no model call) |
| Preflight `--check` | `printf '# test proposal\n' \| python3 scripts/challenge.py --proposal - --vault /opt/second-brain/vault --check` | `pass` (exits 0; resolves note and decisions paths without calling models) |
| Product smoke | `python3 scripts/product_smoke.py --root .` | `pass` (`2/2` steps: `hardcodes`, `unit`) |
