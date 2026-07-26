#!/usr/bin/env bash
# Run harness unit tests without requiring a full venv.
# Always runs stdlib unittest bootstrap tests; runs pytest if available.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== unittest (install + verify_skills) ==="
python3 -m unittest tests.test_install_bootstrap tests.test_verify_skills -v

if python3 -c "import pytest" 2>/dev/null; then
  echo "=== pytest (full suite) ==="
  python3 -m pytest tests/ -q
else
  echo "=== pytest skipped (not installed); bootstrap tests OK ==="
fi

echo "=== verify_skills (harness root) ==="
python3 scripts/verify_skills.py "$ROOT"

echo "✅ harness tests complete"
