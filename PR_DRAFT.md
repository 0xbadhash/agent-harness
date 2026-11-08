# PR draft — night validate_full vault registration

**Spec waiver:** hotfix

## What Problem This Solves

`python3 scripts/validate.py full` exited 1. Vault schema lint rejected `01-Projects/mission-feeds/` because that product was not in `config/night_shift_products.yaml`, and it rejected `01-Projects/product/` because a missing plugin label defaulted to the literal name `product`. The same lint also rejected the live vault's `challenges/` directories, `INDEX.md` files, root `instruction-versions/` and `rules/`, and the files-only `herm-config` stub. `ruff check` failed on an unused import in `scripts/kanban_fs.py`.

## Why This Change Was Made

The night report's two errors are registration and a made-up folder name, not a new product. `mission-feeds` already has `product_id` and `project_label` `mission-feeds` and a checkout at `~/.local/lib/mission-feeds`. The schema allow-list matches directories the vault already uses. `challenge.py` used to write into `/opt/second-brain/vault` when `--vault` and `PRODUCT_VAULT_ROOT` were both unset, which is how a fixture folder landed in the live vault. Refusing that write is smaller than teaching the linter to ignore a fake project.

## User Impact

Overnight `validate_full` for agent-harness can pass against the current vault. Challenge notes are not filed on the host vault unless the operator passes `--vault` or sets `PRODUCT_VAULT_ROOT`. No product UI change. No release, tag, or push.

## Evidence

Red, before the fix: `tests/test_vault_resolve_label.py` expected `01-Projects/widget/...` and got `01-Projects/product/...`. `tests/test_challenge.py::test_unset_vault_refuses_instead_of_host_default` did not raise. Schema tests against the HEAD linter exited 1 (`challenges/` undeclared, `INDEX.md` warning, `instruction-versions/`, `rules/`, `herm-config`). `ruff check` on HEAD `scripts/kanban_fs.py` reported F401. HEAD `night_shift_products.yaml` had no `mission-feeds` row.

Green: those tests passed (17 in the focused set). `python3 scripts/validate.py full` passed 6/6, including vault schema lint with 0 errors and 0 warnings. `ruff check scripts tests` passed.

```text
red_cmd: .venv/bin/python -m pytest -q tests/test_vault_resolve_label.py tests/test_challenge.py::ChallengeTests::test_unset_vault_refuses_instead_of_host_default tests/test_vault_schema_lint_allow.py
green_cmd: .venv/bin/python -m pytest -q tests/test_vault_resolve_label.py tests/test_vault_schema_lint_allow.py tests/test_challenge.py tests/test_night_shift_all_parallel.py tests/test_vault_schema_lint_surface_alias.py
```

## Evidence pack

| Item | Result |
|------|--------|
| pytest | focused 17 passed; validate test_runner exit 0 |
| validate | `python3 scripts/validate.py full` 6/6 |
| hardcodes | check_hardcodes exit 0 |
| ruff | `ruff check scripts tests` exit 0 |

## Traceability

| AC | Test / smoke |
|----|----------------|
| AC-1 mission-feeds is registered with a portable path | tests/test_vault_schema_lint_allow.py::TestVaultSchemaAllow::test_products_yaml_mission_feeds_path_is_portable and tests/test_night_shift_all_parallel.py |
| AC-2 a plugin-less root is not filed as product | tests/test_vault_resolve_label.py::TestProjectRelLabel::test_missing_plugin_uses_directory_name |
| AC-3 unset vault does not use the host default | tests/test_challenge.py::ChallengeTests::test_unset_vault_refuses_instead_of_host_default |
| AC-4 live layout (challenges, INDEX, herm-config, root lodges) passes strict lint and strangers still fail | tests/test_vault_schema_lint_allow.py |
| AC-5 ruff clean on scripts and tests | ruff check scripts tests (F401 removed from scripts/kanban_fs.py) |
| AC-6 validate full | python3 scripts/validate.py full |

## Threat notes

- A missing label used to mkdir `01-Projects/product/` on the live vault. The writer now raises if no vault is configured, and the label comes from the plugin or the checkout directory name.
- `herm-config` is files-only. A subdirectory still fails schema lint. The night-shift plugin stays off until an operator registers it.
- Allowing `challenges/` and `INDEX.md` does not allow an unregistered project folder. `not-a-product` still fails.

## Things that look bad but are actually fine

1. The night proposal to "replace absolute host paths" matched `/home/` in the hardcodes allow printout (`/home/browser` container paths), not a new hardcode. `check_hardcodes` was already exit 0. Those allow-listed container paths stay.
2. `red_cmd` cannot fail again in the same way once the fix is present. The red run was captured before the implementation edit: label `product`, `ValueError` not raised, HEAD schema lint exit 1.
3. `01-Projects/product/` is already absent on disk. This change stops the writer that created it. It does not delete vault files.

## Red proof

```text
red_cmd: .venv/bin/python -m pytest -q tests/test_vault_resolve_label.py tests/test_challenge.py::ChallengeTests::test_unset_vault_refuses_instead_of_host_default tests/test_vault_schema_lint_allow.py
green_cmd: .venv/bin/python -m pytest -q tests/test_vault_resolve_label.py tests/test_vault_schema_lint_allow.py tests/test_challenge.py tests/test_night_shift_all_parallel.py tests/test_vault_schema_lint_surface_alias.py
```
