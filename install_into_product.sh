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
DELETE_STALE=0
PRODUCT_ARG=""
for a in "$@"; do
  case "$a" in
    --verify) VERIFY=1 ;;
    --delete-stale-skills) DELETE_STALE=1 ;;
    -h|--help)
      cat <<'EOF'
Usage: install_into_product.sh [PRODUCT_ROOT] [--verify] [--delete-stale-skills]

  --verify               Run bootstrap_check after install
  --delete-stale-skills  Remove portable skills that no longer exist in harness SoT
                         (never deletes product-only skill directories)

AGENTS_HARNESS_ROOT=... overrides harness source root.
EOF
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

# A4: remove portable skills that were deleted from harness SoT
if [[ "$DELETE_STALE" -eq 1 ]]; then
  mapfile -t PORTABLE < <(find "$HARNESS_ROOT/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
  if [[ ${#PORTABLE[@]} -gt 0 ]]; then
    for d in "$PRODUCT_ROOT/.agents/skills"/*; do
      [[ -d "$d" ]] || continue
      name="$(basename "$d")"
      # only consider names that look like former portable skills: listed in ship_skills
      # or were once under harness (we only delete if NOT in current portable set AND
      # appears in ship_skills history file OR matches known portable set from ship_skills.txt)
      in_portable=0
      for p in "${PORTABLE[@]}"; do
        if [[ "$name" == "$p" ]]; then in_portable=1; break; fi
      done
      if [[ "$in_portable" -eq 1 ]]; then
        continue
      fi
      # Product-only: keep unless name is in STALE_PORTABLE allowlist (skills removed from SoT)
      # Stale portable = not in current harness skills/ but was shipped as portable (ship_skills or known)
      if [[ -f "$HARNESS_ROOT/config/removed_portable_skills.txt" ]] && \
         grep -qxF "$name" "$HARNESS_ROOT/config/removed_portable_skills.txt" 2>/dev/null; then
        rm -rf "$d"
        echo "  - removed stale portable skill: $name"
      fi
    done
  fi
  # Also remove skills that exist neither in harness nor as obvious product-only:
  # safer path: only delete if present in removed_portable_skills.txt (explicit)
  echo "  ~ stale portable skills pruned (see config/removed_portable_skills.txt)"
fi

# Protect product-forked scripts from silent overwrite (night_shift regression class).
# List one relative path per line under PRODUCT_ROOT, e.g. scripts/pipeline_state.py
# Optional also: $HARNESS_ROOT/config/default_protect_scripts.txt (shared defaults).
# IMPORTANT: only exclude when the destination file already exists — fresh installs
# must still receive harness scripts (post-install CRITICAL checks require them).
PROTECT_EX=()
_load_protect() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" ]] && continue
    local rel="$line"
    case "$line" in
      scripts/*) rel="${line#scripts/}" ;;
    esac
    # Skip protect when product has not forked this file yet
    if [[ ! -f "$PRODUCT_ROOT/scripts/$rel" && ! -f "$PRODUCT_ROOT/$line" ]]; then
      continue
    fi
    # rsync --exclude is relative to transfer root (scripts/)
    PROTECT_EX+=(--exclude "$rel")
  done < "$f"
}
_load_protect "$HARNESS_ROOT/config/default_protect_scripts.txt"
_load_protect "$PRODUCT_ROOT/.agents/harness_protect_scripts.txt"
if [[ ${#PROTECT_EX[@]} -gt 0 ]]; then
  echo "  i protecting ${#PROTECT_EX[@]} existing product fork(s) from harness rsync"
fi
rsync -a "${RSYNC_EX[@]}" "${PROTECT_EX[@]}" "$HARNESS_ROOT/scripts/" "$PRODUCT_ROOT/scripts/"
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
for doc in ship-flow.md ship-flow-detailed.md skills-catalog.md llm-bootstrap.md bootstrap.md start-a-feature.md prompt-patterns.md web-e2e-comet.md; do
  if [[ -f "$HARNESS_ROOT/docs/$doc" ]]; then
    cp -a "$HARNESS_ROOT/docs/$doc" "$PRODUCT_ROOT/.agents/docs/$doc"
  fi
done
# Poster diagrams for detailed flow (optional; ignore if missing)
if [[ -d "$HARNESS_ROOT/docs/diagrams" ]]; then
  mkdir -p "$PRODUCT_ROOT/.agents/docs/diagrams"
  rsync -a "$HARNESS_ROOT/docs/diagrams/" "$PRODUCT_ROOT/.agents/docs/diagrams/" 2>/dev/null || \
    cp -a "$HARNESS_ROOT/docs/diagrams/." "$PRODUCT_ROOT/.agents/docs/diagrams/" 2>/dev/null || true
fi
echo "  ~ .agents/docs/ (ship-flow, ship-flow-detailed, skills-catalog, llm-bootstrap, start-a-feature)"
# CI matrix docs (optional mirror)
if [[ -f "$HARNESS_ROOT/docs/ci-matrix.md" ]]; then
  cp -a "$HARNESS_ROOT/docs/ci-matrix.md" "$PRODUCT_ROOT/.agents/docs/ci-matrix.md"
fi

# J1–J5+J7(+J12) product daytime workflow + Semgrep config + ZAP helpers (step 1/3/4)
mkdir -p "$PRODUCT_ROOT/.github/workflows"
if [[ -f "$HARNESS_ROOT/templates/daytime-gates.yml" ]]; then
  # Always refresh template so portfolio force-install picks up fail-closed matrix
  cp -a "$HARNESS_ROOT/templates/daytime-gates.yml" \
    "$PRODUCT_ROOT/.github/workflows/daytime-gates.yml"
  echo "  ~ .github/workflows/daytime-gates.yml (J1–J5+J7+J12)"
fi
if [[ -f "$HARNESS_ROOT/templates/zap-baseline.yml" ]]; then
  if [[ ! -f "$PRODUCT_ROOT/.github/workflows/zap-baseline.yml" ]]; then
    cp -a "$HARNESS_ROOT/templates/zap-baseline.yml" \
      "$PRODUCT_ROOT/.github/workflows/zap-baseline.yml"
    echo "  + .github/workflows/zap-baseline.yml (J13 optional)"
  fi
fi
if [[ -f "$HARNESS_ROOT/.semgrep.yml" ]]; then
  if [[ ! -f "$PRODUCT_ROOT/.semgrep.yml" ]]; then
    cp -a "$HARNESS_ROOT/.semgrep.yml" "$PRODUCT_ROOT/.semgrep.yml"
    echo "  + .semgrep.yml (J12)"
  fi
fi
if [[ -f "$HARNESS_ROOT/scripts/zap_baseline.sh" ]]; then
  cp -a "$HARNESS_ROOT/scripts/zap_baseline.sh" "$PRODUCT_ROOT/scripts/zap_baseline.sh"
  chmod +x "$PRODUCT_ROOT/scripts/zap_baseline.sh" 2>/dev/null || true
fi
if [[ -f "$HARNESS_ROOT/config/zap_targets.yaml" && ! -f "$PRODUCT_ROOT/config/zap_targets.yaml" ]]; then
  mkdir -p "$PRODUCT_ROOT/config"
  cp -a "$HARNESS_ROOT/config/zap_targets.yaml" "$PRODUCT_ROOT/config/zap_targets.yaml"
  echo "  + config/zap_targets.yaml (J13 targets — edit URLs)"
fi

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
if [[ -f "$HARNESS_ROOT/VERSION" ]]; then
  cp -a "$HARNESS_ROOT/VERSION" "$PRODUCT_ROOT/.agents/HARNESS_VERSION"
  echo "  ~ .agents/HARNESS_VERSION=$(tr -d '\n' < "$HARNESS_ROOT/VERSION")"
fi

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
# Website/app products: fail-closed E2E contract (Playwright + Comet) — see docs/web-e2e-comet.md
if [[ -f "$PRODUCT_ROOT/scripts/check_web_e2e.py" ]]; then
  echo "   Web E2E: python3 scripts/check_web_e2e.py --root .  (mandatory if website/app detected)"
  if python3 "$PRODUCT_ROOT/scripts/check_web_e2e.py" --root "$PRODUCT_ROOT" >/tmp/web_e2e_install_check.txt 2>&1; then
    echo "   Web E2E check: ok (or no website)"
  else
    echo "   ⚠️  Web E2E check FAILED — product has website/app but contract incomplete:"
    sed 's/^/      /' /tmp/web_e2e_install_check.txt | tail -20
    echo "      Fix before /pr_review or set web_e2e.enabled: false if CLI-only. Docs: .agents/docs/web-e2e-comet.md"
  fi
fi

if [[ "$VERIFY" -eq 1 ]]; then
  echo "--- --verify ---"
  bash "$PRODUCT_ROOT/scripts/bootstrap_check.sh" "$PRODUCT_ROOT"
fi

# Drop bytecode from rsync leak or verify probes (products should not vendor __pycache__)
find "$PRODUCT_ROOT/scripts" "$PRODUCT_ROOT/.agents" \
  \( -type d -name '__pycache__' -o -type f -name '*.py[cod]' \) \
  -print0 2>/dev/null | xargs -0r rm -rf
