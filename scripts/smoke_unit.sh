#!/usr/bin/env bash
# Portable unit smoke for agent-harness (and products that copy this script).
# Avoid nested bash -c / YAML quote hell under product_smoke + night_shift.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

resolve_python() {
  if [[ -n "${COMPLIANCE_PYTHON:-}" && -x "${COMPLIANCE_PYTHON}" ]]; then
    echo "${COMPLIANCE_PYTHON}"
    return
  fi
  if [[ -n "${COMPLIANCE_PYTHON:-}" ]]; then
    # path may be relative or bare name
    if command -v "${COMPLIANCE_PYTHON}" >/dev/null 2>&1; then
      command -v "${COMPLIANCE_PYTHON}"
      return
    fi
  fi
  if [[ -x "${HOME}/watchlist/.venv/bin/python" ]]; then
    echo "${HOME}/watchlist/.venv/bin/python"
    return
  fi
  if [[ -x "${ROOT}/.venv/bin/python" ]]; then
    echo "${ROOT}/.venv/bin/python"
    return
  fi
  if [[ -x "${ROOT}/venv/bin/python" ]]; then
    echo "${ROOT}/venv/bin/python"
    return
  fi
  command -v python3
}

if [[ "${1:-}" == "--print-python" ]]; then
  resolve_python
  exit 0
fi

PY="$(resolve_python)"
# Prefer pytest module; fall back to unittest discover if pytest missing
if "$PY" -c "import pytest" 2>/dev/null; then
  exec "$PY" -m pytest -q "$@"
fi
exec "$PY" -m unittest discover -s tests -q
