#!/usr/bin/env bash
# ORCH-TOOLS: single entry for type/lint/test/hygiene (+ optional real coverage).
# SoT: agent-harness. Install into products via install_into_product.sh (tools/).
#
# Usage (from product or harness root):
#   ./tools/bin/lint_and_test.sh
#   ./tools/bin/lint_and_test.sh --coverage
#   LINT_AND_TEST_COVERAGE=1 ./tools/bin/lint_and_test.sh
set -euo pipefail

# tools/bin → repo root
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi

echo "== lint_and_test: validate full =="
"$PY" "$ROOT/scripts/validate.py" full

RUN_COV=0
for arg in "$@"; do
  case "$arg" in
    --coverage|-c) RUN_COV=1 ;;
  esac
done
if [[ "${LINT_AND_TEST_COVERAGE:-0}" == "1" ]]; then
  RUN_COV=1
fi

if [[ "$RUN_COV" == "1" ]]; then
  echo "== lint_and_test: coverage --run =="
  # Soft if tooling missing so green machines without pytest-cov still work
  "$PY" "$ROOT/scripts/check_module_coverage.py" --run --soft-if-missing \
    || "$PY" "$ROOT/scripts/check_module_coverage.py" --run
fi

echo "✅ lint_and_test complete"
