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
need "scripts/product_plugin.py"
need "scripts/product_venv.py"
need "scripts/review_scope.py"
need "scripts/next_skill.py"
need "scripts/verify_skills.py"

if [[ -f scripts/pipeline_state.py ]]; then
  python3 scripts/pipeline_state.py get || fail=1
fi

if [[ -f scripts/verify_skills.py ]]; then
  python3 scripts/verify_skills.py "$ROOT" || fail=1
fi

if [[ -f scripts/next_skill.py ]]; then
  # review_scope is a hard import of next_skill — do not hide failures
  # Per-product err file so concurrent bootstrap_check runs do not clobber each other
  ns_err="$ROOT/.agents/traces/.bootstrap_next_skill.err"
  mkdir -p "$(dirname "$ns_err")"
  set +e
  out=$(python3 scripts/next_skill.py --after execute_dev --base HEAD --head HEAD 2>"$ns_err")
  ns_rc=$?
  set -e
  echo "  next after execute_dev: $out"
  if [[ $ns_rc -ne 0 ]]; then
    echo "  ❌ next_skill exited $ns_rc"
    if [[ -s "$ns_err" ]]; then
      sed -n '1,20p' "$ns_err" | sed 's/^/    /'
    fi
    fail=1
  elif [[ -z "$out" ]]; then
    echo "  ❌ next_skill produced empty output"
    fail=1
  elif [[ "$out" != NEXT_SKILL=* ]]; then
    echo "  ❌ next_skill stdout must be NEXT_SKILL=… (got: $out)"
    fail=1
  else
    echo "  ✅ next_skill OK"
  fi
  rm -f "$ns_err"
fi

if [[ $fail -ne 0 ]]; then
  echo "❌ bootstrap_check FAILED"
  exit 1
fi
echo "✅ bootstrap_check OK — LLM can load skills under .agents/skills/ and run full FSM"
exit 0
