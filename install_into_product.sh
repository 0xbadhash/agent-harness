#!/usr/bin/env bash
# Install portable harness into a product git root (cwd or $1).
set -euo pipefail

HARNESS_ROOT="$(cd "$(dirname "$0")" && pwd)"
PRODUCT_ROOT="$(cd "${1:-.}" && pwd)"

echo "Harness: $HARNESS_ROOT"
echo "Product: $PRODUCT_ROOT"

mkdir -p \
  "$PRODUCT_ROOT/.agents/state" \
  "$PRODUCT_ROOT/.agents/traces" \
  "$PRODUCT_ROOT/.agents/artifacts" \
  "$PRODUCT_ROOT/.agents/skills" \
  "$PRODUCT_ROOT/.agents/policy" \
  "$PRODUCT_ROOT/scripts"

if [[ ! -f "$PRODUCT_ROOT/.agents/state/pipeline.json" ]]; then
  cp -a "$HARNESS_ROOT/templates/pipeline.json" "$PRODUCT_ROOT/.agents/state/pipeline.json"
  echo "  + pipeline.json (init)"
fi

# Overwrite portable skills only; never delete product-only skill directories
rsync -a "$HARNESS_ROOT/skills/" "$PRODUCT_ROOT/.agents/skills/"
echo "  ~ skills/ (portable skills refreshed; product-only dirs kept)"

rsync -a "$HARNESS_ROOT/scripts/" "$PRODUCT_ROOT/scripts/"
echo "  ~ scripts/"

rsync -a "$HARNESS_ROOT/policy/" "$PRODUCT_ROOT/.agents/policy/"
echo "  ~ .agents/policy/"

if [[ ! -f "$PRODUCT_ROOT/.agents/product_plugin.yaml" ]]; then
  cp -a "$HARNESS_ROOT/product_plugin.example.yaml" "$PRODUCT_ROOT/.agents/product_plugin.yaml"
  echo "  + product_plugin.yaml (edit me)"
else
  echo "  = product_plugin.yaml exists (left as-is)"
fi

echo "$HARNESS_ROOT" > "$PRODUCT_ROOT/.agents/HARNESS_ROOT"
date -u +%Y-%m-%dT%H:%M:%SZ > "$PRODUCT_ROOT/.agents/HARNESS_INSTALLED_AT"
echo "✅ installed portable harness into $PRODUCT_ROOT"
