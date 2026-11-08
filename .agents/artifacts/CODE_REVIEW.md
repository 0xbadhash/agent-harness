# CODE-REVIEW

**Marker:** CODE-REVIEW
**Base:** parent of this commit
**Head:** night validate_full hotfix
**Verdict:** approve
**P0:** 0

## Scope

In this ship: `config/night_shift_products.yaml`, `scripts/vault_schema_lint.py`, `scripts/vault_resolve.py`, `scripts/challenge.py`, `scripts/kanban_fs.py`, the new label and schema tests, `tests/test_challenge.py`, `tests/test_night_shift_all_parallel.py`, `CHANGELOG.md`, `PR_DRAFT.md`.

Left unstaged on purpose: `scripts/ops_dashboard.py`, `tests/test_ops_dashboard.py`, `.gitignore`, `config/optional_skills.txt`, and untracked local files. They are not part of this hotfix.

## Secrets

`python3 scripts/check_hardcodes.py` exit 0 during `validate.py full`. No new absolute user path. The challenge host fallback `/opt/second-brain/vault` was removed.

## Findings

| ID | Class | Verdict |
|----|--------|---------|
| P0 | none | approve |

Checked:

- `project_rel` no longer treats the default label `product` as a real plugin label. A directory with no plugin uses that directory's name. An explicit `project_label` still wins.
- `challenge._vault_paths` raises when `--vault` and `PRODUCT_VAULT_ROOT` are both unset. It does not mkdir on the host vault.
- Schema allow-list is narrow: `herm-config` is files-only and a subdirectory still fails. An unregistered project name still fails. `challenges/` and `INDEX.md` match files the live vault already has.
- `mission-feeds: ~/.local/lib/mission-feeds` is a `~/` path, and the plugin `project_label` is `mission-feeds`.
- `kanban_fs.py` only drops an unused import. Ruff on HEAD reported F401 and `--fix` is that deletion.

## Follow-ups (not in this diff)

- `scripts/sync_docs_full.py`, `scripts/sync_vault_devlog.py`, and `night_shift_readiness._safe_label` still contain a `"product"` fallback for an empty label. This hotfix stops the challenge/project_rel writer that the vault folder came from. Those other fallbacks are pre-existing.
- The night "replace absolute host paths" proposal matched `/home/browser` lines that `check_hardcodes` already allow-lists. Not changed.

## Tests

Focused pytest 17 passed. `validate.py full` 6/6 before the changelog edit. `ruff check scripts tests` exit 0.
