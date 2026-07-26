#!/usr/bin/env bash
# Install portable harness into a product git root (cwd or $1).
#
# Usage:
#   ./install_into_product.sh /path/to/product
#   ./install_into_product.sh /path/to/product --verify
#   AGENTS_HARNESS_ROOT=... ./install_into_product.sh .
#
# Any LLM that reads product AGENTS.md + .agents/skills/*/SKILL.md can run the ship FSM.
set -euo pipefail

# Prefer AGENTS_HARNESS_ROOT when set (documented interface); else script location.
if [[ -n "${AGENTS_HARNESS_ROOT:-}" ]]; then
  HARNESS_ROOT="$(cd "$AGENTS_HARNESS_ROOT" && pwd)"
else
  HARNESS_ROOT="$(cd "$(dirname "$0")" && pwd)"
fi
VERIFY=0
PRODUCT_ARG=""
for a in "$@"; do
  case "$a" in
    --verify) VERIFY=1 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0
      ;;
    *)
      if [[ -z "$PRODUCT_ARG" && "$a" != -* ]]; then
        PRODUCT_ARG="$a"
      fi
      ;;
  esac
done
PRODUCT_ROOT="$(cd "${PRODUCT_ARG:-.}" && pwd)"

echo "Harness: $HARNESS_ROOT"
echo "Product: $PRODUCT_ROOT"

if [[ ! -d "$HARNESS_ROOT/skills" || ! -d "$HARNESS_ROOT/scripts" ]]; then
  echo "❌ HARNESS_ROOT does not look like agent-harness (missing skills/ or scripts/): $HARNESS_ROOT" >&2
  exit 1
fi

mkdir -p \
  "$PRODUCT_ROOT/.agents/state" \
  "$PRODUCT_ROOT/.agents/traces" \
  "$PRODUCT_ROOT/.agents/artifacts" \
  "$PRODUCT_ROOT/.agents/skills" \
  "$PRODUCT_ROOT/.agents/policy" \
  "$PRODUCT_ROOT/scripts" \
  "$PRODUCT_ROOT/tools/bin"

if [[ ! -f "$PRODUCT_ROOT/.agents/state/pipeline.json" ]]; then
  cp -a "$HARNESS_ROOT/templates/pipeline.json" "$PRODUCT_ROOT/.agents/state/pipeline.json"
  echo "  + pipeline.json (init)"
fi

# Exclude bytecode so concurrent/partial installs do not leave stale .pyc as SoT
RSYNC_EX=(--exclude '__pycache__/' --exclude '*.py[cod]' --exclude '.pytest_cache/')

# Overwrite portable skills only; never delete product-only skill directories
rsync -a "${RSYNC_EX[@]}" "$HARNESS_ROOT/skills/" "$PRODUCT_ROOT/.agents/skills/"
echo "  ~ skills/ (portable skills refreshed; product-only dirs kept)"

rsync -a "${RSYNC_EX[@]}" "$HARNESS_ROOT/scripts/" "$PRODUCT_ROOT/scripts/"
echo "  ~ scripts/"

rsync -a "${RSYNC_EX[@]}" "$HARNESS_ROOT/policy/" "$PRODUCT_ROOT/.agents/policy/"
echo "  ~ .agents/policy/"

# Ship-skill manifest for verify_skills
if [[ -f "$HARNESS_ROOT/config/ship_skills.txt" ]]; then
  mkdir -p "$PRODUCT_ROOT/.agents/policy"
  cp -a "$HARNESS_ROOT/config/ship_skills.txt" "$PRODUCT_ROOT/.agents/policy/ship_skills.txt"
  echo "  ~ .agents/policy/ship_skills.txt"
fi

# Progressive-disclosure docs for any LLM (optional mirror under .agents/docs)
mkdir -p "$PRODUCT_ROOT/.agents/docs"
for doc in ship-flow.md skills-catalog.md llm-bootstrap.md bootstrap.md; do
  if [[ -f "$HARNESS_ROOT/docs/$doc" ]]; then
    cp -a "$HARNESS_ROOT/docs/$doc" "$PRODUCT_ROOT/.agents/docs/$doc"
  fi
done
echo "  ~ .agents/docs/ (ship-flow, skills-catalog, llm-bootstrap)"

if [[ -d "$HARNESS_ROOT/tools" ]]; then
  rsync -a "${RSYNC_EX[@]}" "$HARNESS_ROOT/tools/" "$PRODUCT_ROOT/tools/"
  chmod +x "$PRODUCT_ROOT/tools/bin/"*.sh 2>/dev/null || true
  echo "  ~ tools/ (lint_and_test etc.)"
fi

if [[ ! -f "$PRODUCT_ROOT/.agents/product_plugin.yaml" ]]; then
  cp -a "$HARNESS_ROOT/product_plugin.example.yaml" "$PRODUCT_ROOT/.agents/product_plugin.yaml"
  echo "  + product_plugin.yaml (edit me — stack + smoke)"
else
  echo "  = product_plugin.yaml exists (left as-is)"
fi

# AGENTS.md: append harness pointer if file missing; never overwrite product AGENTS
if [[ ! -f "$PRODUCT_ROOT/AGENTS.md" ]]; then
  if [[ -f "$HARNESS_ROOT/templates/AGENTS.harness.md" ]]; then
    cp -a "$HARNESS_ROOT/templates/AGENTS.harness.md" "$PRODUCT_ROOT/AGENTS.md"
    echo "  + AGENTS.md (from harness template — edit for product intent)"
  fi
else
  echo "  = AGENTS.md exists (left as-is)"
fi

if [[ -f "$HARNESS_ROOT/templates/CONSTITUTION.example.md" && ! -f "$PRODUCT_ROOT/.agents/CONSTITUTION.md" ]]; then
  echo "  i optional: cp templates/CONSTITUTION.example.md → .agents/CONSTITUTION.md"
fi

chmod +x "$PRODUCT_ROOT/scripts/"*.py 2>/dev/null || true
chmod +x "$PRODUCT_ROOT/scripts/bootstrap_check.sh" 2>/dev/null || true

# Always assert critical FSM files landed (catches partial rsync / wrong HARNESS_ROOT)
CRITICAL=(
  "scripts/next_skill.py"
  "scripts/review_scope.py"
  "scripts/verify_skills.py"
  "scripts/bootstrap_check.sh"
  "scripts/product_smoke.py"
  "scripts/product_plugin.py"
  "scripts/product_venv.py"
  "scripts/pipeline_state.py"
  "scripts/pr_validator.py"
  ".agents/skills/execute_dev/SKILL.md"
  ".agents/skills/code_review/SKILL.md"
  ".agents/skills/behavior_validator/SKILL.md"
  ".agents/skills/pr_review/SKILL.md"
  ".agents/product_plugin.yaml"
  ".agents/state/pipeline.json"
)
miss=0
for rel in "${CRITICAL[@]}"; do
  if [[ ! -e "$PRODUCT_ROOT/$rel" ]]; then
    echo "  ❌ post-install missing: $rel" >&2
    miss=1
  fi
done
if [[ "$miss" -ne 0 ]]; then
  echo "❌ install incomplete under $PRODUCT_ROOT" >&2
  exit 1
fi

echo "$HARNESS_ROOT" > "$PRODUCT_ROOT/.agents/HARNESS_ROOT"
date -u +%Y-%m-%dT%H:%M:%SZ > "$PRODUCT_ROOT/.agents/HARNESS_INSTALLED_AT"

# Count ship skills
SHIP_N=0
SHIP_EXPECT=0
if [[ -f "$PRODUCT_ROOT/.agents/policy/ship_skills.txt" ]]; then
  while read -r s; do
    [[ -z "$s" || "$s" == \#* ]] && continue
    SHIP_EXPECT=$((SHIP_EXPECT + 1))
    if [[ -f "$PRODUCT_ROOT/.agents/skills/$s/SKILL.md" ]]; then
      SHIP_N=$((SHIP_N + 1))
    else
      echo "  ❌ ship skill missing after install: $s" >&2
      miss=1
    fi
  done < "$PRODUCT_ROOT/.agents/policy/ship_skills.txt"
fi
if [[ "$miss" -ne 0 ]]; then
  echo "❌ install incomplete under $PRODUCT_ROOT" >&2
  exit 1
fi

echo "✅ installed portable harness into $PRODUCT_ROOT"
echo "   ship skills installed (manifest hits): $SHIP_N / $SHIP_EXPECT"
echo "   FSM docs: .agents/docs/ship-flow.md · llm-bootstrap.md"
echo "   Verify:  bash scripts/bootstrap_check.sh"
echo "   Any LLM: read AGENTS.md + .agents/skills/*/SKILL.md; run ship chain in llm-bootstrap.md"

if [[ "$VERIFY" -eq 1 ]]; then
  echo "--- --verify ---"
  bash "$PRODUCT_ROOT/scripts/bootstrap_check.sh" "$PRODUCT_ROOT"
fi

# Drop bytecode from rsync leak or verify probes (products should not vendor __pycache__)
find "$PRODUCT_ROOT/scripts" "$PRODUCT_ROOT/.agents" \
  \( -type d -name '__pycache__' -o -type f -name '*.py[cod]' \) \
  -print0 2>/dev/null | xargs -0r rm -rf
