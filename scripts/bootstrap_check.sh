#!/usr/bin/env bash
# Post-install health check for a product (or harness) root.
# Usage: bootstrap_check.sh [product_root]
set -euo pipefail

ROOT="$(cd "${1:-.}" && pwd)"
cd "$ROOT"

echo "=== bootstrap_check: $ROOT ==="
fail=0

need() {
  if [[ -e "$1" ]]; then
    echo "  ✅ $1"
  else
    echo "  ❌ missing $1"
    fail=1
  fi
}

need ".agents/product_plugin.yaml"
need ".agents/state/pipeline.json"
need ".agents/skills/execute_dev/SKILL.md"
need ".agents/skills/pr_review/SKILL.md"
need ".agents/skills/release_mgmt/SKILL.md"
need ".agents/skills/sync_docs/SKILL.md"
need ".agents/skills/code_review/SKILL.md"
need ".agents/skills/behavior_validator/SKILL.md"
need "scripts/pipeline_state.py"
need "scripts/pr_validator.py"
need "scripts/product_smoke.py"
need "scripts/next_skill.py"
need "scripts/verify_skills.py"

if [[ -f scripts/pipeline_state.py ]]; then
  python3 scripts/pipeline_state.py get || fail=1
fi

if [[ -f scripts/verify_skills.py ]]; then
  python3 scripts/verify_skills.py "$ROOT" || fail=1
fi

if [[ -f scripts/next_skill.py ]]; then
  out=$(python3 scripts/next_skill.py --after execute_dev --base HEAD --head HEAD 2>/dev/null || true)
  echo "  next after execute_dev: $out"
  if [[ -z "$out" ]]; then
    echo "  ⚠️  next_skill produced empty output"
  fi
fi

if [[ $fail -ne 0 ]]; then
  echo "❌ bootstrap_check FAILED"
  exit 1
fi
echo "✅ bootstrap_check OK — LLM can load skills under .agents/skills/ and run full FSM"
exit 0
