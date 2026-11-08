# BEHAVIOR-CONTRACT

**Marker:** BEHAVIOR-CONTRACT
**Surface:** vault schema lint CLI and the night-shift product registry

## Clauses

1. `python3 scripts/vault_schema_lint.py --vault /opt/second-brain/vault --strict-warn` exits 0 and prints `0 error(s), 0 warning(s)`.
2. `config/night_shift_products.yaml` has a `mission-feeds:` row whose path starts with `~/` and does not contain `/home/`.
3. `01-Projects/product` is not a directory in the live vault.
4. `ruff check scripts tests` exits 0.
